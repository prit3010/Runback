import { BaseNode } from "@/components/dag/nodes/base-node";
export function ErrorNode(props: { data: any }) {
  return <BaseNode {...props} tone="border-red-400" />;
}
