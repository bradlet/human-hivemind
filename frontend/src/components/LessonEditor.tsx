import CodeMirror from "@uiw/react-codemirror";
import { markdown } from "@codemirror/lang-markdown";

export default function LessonEditor({
  value,
  onChange,
  height = "60vh",
}: {
  value: string;
  onChange: (v: string) => void;
  height?: string;
}) {
  return (
    <div className="border border-ink-300 rounded overflow-hidden">
      <CodeMirror
        value={value}
        height={height}
        extensions={[markdown()]}
        onChange={(v) => onChange(v)}
        basicSetup={{ lineNumbers: true, foldGutter: true }}
      />
    </div>
  );
}
