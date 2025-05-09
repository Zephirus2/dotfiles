
from .app_iface import *
from .utils import ShadowedCollectionProperty


class CopyFromMixin:

    TYPES_MAP = {'BOOLEAN': bool, 'INT': int, 'FLOAT': float, 'STRING': str, 'ENUM': str}
    IGNORED_PROPS = {'rna_type'}

    def copy_from(self, other):
        for prop_id, prop_struct in AppInterface.object_property_data(self).items():
            if prop_id in self.IGNORED_PROPS:
                continue
    
            if prop_struct.type in {'POINTER', 'COLLECTION'}:
                getattr(self, prop_id).copy_from(getattr(other, prop_id))
            else:
                py_type = self.TYPES_MAP[prop_struct.type]
                setattr(self, prop_id, py_type(getattr(other, prop_id)))


class StandalonePropertyGroupBase(CopyFromMixin):

    @property
    def bl_rna(self):
        return self._pg_cls.bl_rna
    
    def cast_setattr(self, key, value):
        _types_func = {'BOOLEAN': bool, 'INT': int, 'FLOAT': float, 'STRING': str, 'ENUM': str}

    def __init__(self):
        # print(AppInterface.object_property_data(self).items())
        for prop_id, prop_struct in AppInterface.object_property_data(self).items():
            if prop_id in self.IGNORED_PROPS:
                continue

            prop_val = None

            if prop_struct.type == 'POINTER':
                prop_val = prop_struct.fixed_type.SA()

            elif prop_struct.type == 'COLLECTION':
                prop_val = ShadowedCollectionProperty(elem_type=prop_struct.fixed_type.SA)

            elif prop_struct.type == 'ENUM':
                prop_val = str(prop_struct.enum_items.keys()[0])

            else:
                py_type = self.TYPES_MAP[prop_struct.type]
                prop_val = py_type(prop_struct.default)

            assert prop_val is not None
            setattr(self, prop_id, prop_val)

    def cast_setattr(self, key, value):
        def _cast_value(_value, _type):
            _cast_func = self.TYPES_MAP.get(_type)
            if _cast_func is None:
                return _value
            return _cast_func(_value)

        prop_struct = AppInterface.object_property_data(self).get(key, None)
        if prop_struct is not None and prop_struct.type in self.TYPES_MAP:
            prop_type = prop_struct.type
            is_array = getattr(prop_struct, 'is_array', False)
            if is_array:
                value = type(value)(_cast_value(v, prop_type) for v in value)
            else:
                value = _cast_value(value, prop_type)
        super().__setattr__(key, value)

    def property_unset(self, prop_name):
        prop_struct = AppInterface.object_property_data(self)[prop_name]
        is_array = getattr(prop_struct, 'is_array', False)
        if is_array and hasattr(prop_struct, 'default_array'):
            setattr(self, prop_name, prop_struct.default_array)
        elif hasattr(prop_struct, 'default'):
            setattr(self, prop_name, prop_struct.default)


def standalone_property_group(new_cls):
    pg_dict = dict()
    pg_exclude = { '__init__' }

    for id, value in new_cls.__dict__.items():
        if id not in pg_exclude:
            pg_dict[id] = value

    pg_cls = type(new_cls.__name__, (PropertyGroup, CopyFromMixin) + new_cls.__bases__, pg_dict)
    sa_cls = type(new_cls.__name__ + '_SA', (StandalonePropertyGroupBase,) + new_cls.__bases__, dict(new_cls.__dict__))
    pg_cls.SA = sa_cls
    sa_cls._pg_cls = pg_cls
    return pg_cls
