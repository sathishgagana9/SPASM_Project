import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose prose-invert prose-sm max-w-none prose-p:my-2 prose-pre:my-2 prose-pre:bg-lab-bg prose-pre:border prose-pre:border-lab-border prose-code:text-lab-accent prose-headings:text-slate-100 prose-a:text-lab-accent">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
