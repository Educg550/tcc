import { EditorView } from "codemirror"

export const myTheme = EditorView.theme({
  "&": {
    fontFamily: "monospace !important",
    fontSize: "14px !important",
    backgroundColor: "var(--background-color) !important",
    color: "var(--high-emphasis-color) !important"
  },
".cm-editor": {
    outline: "none"
  },
  ".cm-editor.cm-focused": {
    outline: "none"
  },
  ".cm-activeLine": {
    backgroundColor: "color-mix(in srgb, --primary-color 10%, transparent)"
  },
  ".cm-activeLineGutter": {
    backgroundColor: "var(--surface-color)"
  },
  ".cm-gutters": {
    backgroundColor: "var(--background-color) !important",
    color: "var(--high-emphasis-color) !important",
    display: "flex !important" ,
    border: "0px solid var(--border-color)"
  },
  ".cm-foldPlaceholder": {
    backgroundColor: "var(--surface-color) !important",
    color: "var(--high-emphasis-color) !important",
    border: "1px solid var(--border-color)"
  },
  ".cm-lineNumbers": {
    display: "none !important" 
  },
  ".cm-lintRange": {
    backgroundColor: "color-mix(in srgb, var(--error-color) 20%, transparent)",
  },
  ".cm-lintMarker": {
    color: "var(--error-color)"
  },
  ".cm-tooltip": {
    backgroundColor: "var(--surface-color)",
    color: "var(--high-emphasis-color)",
    boxShadow: "0 2px 5px var(--shadow-color)",
    border: "1px solid var(--border-color)"
  },
  ".cm-diagnostic-error": {
    borderLeft: "5px solid var(--error-color)"
  }
});