"use client";

import { useRouter } from "next/navigation";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";

export function CommandPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const router = useRouter();
  const go = (path: string) => {
    router.push(path);
    onOpenChange(false);
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0">
        <DialogTitle className="sr-only">Command palette</DialogTitle>
        <Command>
          <CommandInput placeholder="Jump to page or action" />
          <CommandList>
            <CommandEmpty>No commands found.</CommandEmpty>
            <CommandGroup heading="Navigation">
              <CommandItem onSelect={() => go("/")}>Dashboard</CommandItem>
              <CommandItem onSelect={() => go("/flows")}>Flows</CommandItem>
              <CommandItem onSelect={() => go("/runs")}>Runs</CommandItem>
              <CommandItem onSelect={() => go("/runners")}>Runners</CommandItem>
              <CommandItem onSelect={() => go("/side-effects")}>Side effects</CommandItem>
            </CommandGroup>
            <CommandGroup heading="Theme">
              <CommandItem onSelect={() => document.documentElement.classList.toggle("dark")}>Toggle dark mode</CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
