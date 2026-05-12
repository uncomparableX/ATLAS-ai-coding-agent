"use client";

import { FileNode } from "@/types";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { ChevronRight, File, Folder, FolderOpen } from "lucide-react";

interface FileTreeProps {
  nodes: FileNode[];
  onSelect?: (node: FileNode) => void;
  selectedPath?: string;
  className?: string;
}

function FileTreeNode({
  node,
  depth = 0,
  onSelect,
  selectedPath,
}: {
  node: FileNode;
  depth?: number;
  onSelect?: (node: FileNode) => void;
  selectedPath?: string;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isSelected = selectedPath === node.path;
  const isDir = node.type === "directory";

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: depth * 0.05 }}
        className={cn(
          "flex items-center gap-1.5 py-1 px-2 rounded-md cursor-pointer text-sm transition-colors",
          isSelected && "bg-accent/10 text-accent",
          !isSelected && "text-muted-foreground hover:text-foreground hover:bg-white/[0.03]"
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => {
          if (isDir) setExpanded(!expanded);
          onSelect?.(node);
        }}
      >
        {isDir && (
          <motion.span
            animate={{ rotate: expanded ? 90 : 0 }}
            className="text-muted-foreground/50"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </motion.span>
        )}
        {!isDir && <span className="w-3.5" />}
        
        {isDir ? (
          expanded ? (
            <FolderOpen className="w-4 h-4 text-accent/70" />
          ) : (
            <Folder className="w-4 h-4 text-muted-foreground/50" />
          )
        ) : (
          <File className="w-4 h-4 text-muted-foreground/50" />
        )}
        
        <span className="truncate">{node.name}</span>
        {node.language && (
          <span className="ml-auto text-[10px] text-muted-foreground/40 px-1.5 py-0.5 rounded bg-white/[0.03]">
            {node.language}
          </span>
        )}
      </motion.div>

      <AnimatePresence>
        {isDir && expanded && node.children && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {node.children.map((child) => (
              <FileTreeNode
                key={child.id}
                node={child}
                depth={depth + 1}
                onSelect={onSelect}
                selectedPath={selectedPath}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function FileTree({ nodes, onSelect, selectedPath, className }: FileTreeProps) {
  return (
    <div className={cn("overflow-auto", className)}>
      {nodes.map((node) => (
        <FileTreeNode
          key={node.id}
          node={node}
          onSelect={onSelect}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  );
}
