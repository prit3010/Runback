import { JsonRenderer } from "@/components/artifact-viewer/json-renderer";

export function InputSection({ value }: { value?: unknown }) {
  return <JsonRenderer content={value ?? {}} />;
}
