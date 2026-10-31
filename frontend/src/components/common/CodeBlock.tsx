import { Copy } from "lucide-react";
import { useState } from "react";

const TOKEN = /(#.*|\/\/.*|"[^"\n]*"|'[^'\n]*'|\b(?:def|async|await|import|from|return|try|except|if|else|elif|for|while|raise|class|const|let|function|with|as|in|not|and|or|None|True|False|new|throw|catch)\b)/g;

function highlight(code: string) {
  return code.split(TOKEN).map((part, i) => {
    if (i % 2 === 0) return part;
    const tone = /^(#|\/\/)/.test(part) ? "text-muted" : /^["']/.test(part) ? "text-ok" : "text-accent";
    return <span key={i} className={tone}>{part}</span>;
  });
}

export default function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="rounded-md border border-line bg-bg">
      <div className="flex items-center justify-between border-b border-line px-3 py-1.5 text-xs text-ink2">
        <span className="mono">{language}</span>
        <button className="inline-flex items-center gap-1 hover:text-ink" onClick={copy}>
          <Copy size={12} /> {copied ? "Copied" : "Copy code"}
        </button>
      </div>
      <pre className="mono overflow-x-auto p-3 leading-5"><code>{highlight(code)}</code></pre>
    </div>
  );
}
