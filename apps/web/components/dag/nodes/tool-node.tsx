import { BaseNode } from "@/components/dag/nodes/base-node";
export function ToolNode(props: { data: any }) {
  return <BaseNode {...props} tone="border-zinc-300" />;
}
