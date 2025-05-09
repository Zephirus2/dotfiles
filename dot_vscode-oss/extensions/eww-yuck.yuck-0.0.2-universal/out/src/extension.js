'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = void 0;
var vscode = require("vscode");
function activate(context) {
    vscode.languages.registerDocumentFormattingEditProvider('yuck', {
        provideDocumentFormattingEdits: function (document) {
            var lines = [];
            var edits = [];
            for (var i = 0; i < document.lineCount; i++) {
                var line = document.lineAt(i);
                lines.push(line.text.trim());
            }
            var indents = 0;
            for (var i = 0; i < lines.length; i++) {
                var workingLine = lines[i];
                var openers = (workingLine.match(/\(/g) || []).length;
                var closers = (workingLine.match(/\)/g) || []).length;
                var replacementLine = "  ".repeat(indents) + workingLine;
                if (openers == 0 && closers > 0) {
                    replacementLine = "  ".repeat(indents - 1) + workingLine;
                }
                replacementLine = replacementLine.replace(/\)\)/, ')\n)');
                edits.push(vscode.TextEdit.replace(document.lineAt(i).range, replacementLine));
                if (openers > closers) {
                    indents += openers - closers;
                }
                else if (closers > openers) {
                    indents -= closers - openers;
                }
            }
            return edits;
        }
    });
}
exports.activate = activate;
//# sourceMappingURL=extension.js.map