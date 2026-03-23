import React from 'react';
import {
  BookOpen,
  Boxes,
  Bot,
  ClipboardList,
  Container,
  Database,
  History,
  LayoutDashboard,
  Settings2,
  Wrench,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { DOCS_CONFIG, DOC_IDS, DocId } from '../constants/docs';
import { cn } from '../lib/utils';
import { Heading } from '../App';

interface SidebarProps {
  activeDoc: DocId;
  onDocSelect: (id: DocId) => void;
  isOpen: boolean;
  onClose: () => void;
  allHeadings: Record<DocId, Heading[]>;
  activeHeadingId: string | null;
}

const navigationIcons: Record<DocId, React.ComponentType<{ className?: string }>> = {
  overview: BookOpen,
  'architecture-design': Boxes,
  'docker-setup': Container,
  'manual-setup': Wrench,
  configuration: Settings2,
  'ai-evaluation-tool': Bot,
  tdms: Database,
  pqet: ClipboardList,
  'execution-dashboard': LayoutDashboard,
  'project-history': History,
};

const navigation = DOC_IDS.map((id) => ({
  id,
  name: DOCS_CONFIG[id].navTitle ?? DOCS_CONFIG[id].title,
  icon: navigationIcons[id],
}));

export function Sidebar({ activeDoc, onDocSelect, isOpen, onClose, allHeadings, activeHeadingId }: SidebarProps) {
  const scrollToHeading = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      onClose();
    }
  };

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-zinc-900/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar Content */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 w-72 bg-sidebar-background border-r border-sidebar-border z-50 transform transition-transform duration-300 lg:translate-x-0 lg:static lg:block lg:h-[calc(100vh-4rem)]",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Nav Links */}
          <nav className="flex-1 overflow-y-auto px-4 py-4 space-y-1 scrollbar-thin scrollbar-thumb-sidebar-border">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = activeDoc === item.id;

              return (
                <div key={item.id} className="space-y-1">
                  <button
                    onClick={() => {
                      onDocSelect(item.id as DocId);
                    }}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors group",
                      isActive
                        ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-md shadow-sidebar-ring/20"
                        : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                    )}
                    >
                      <Icon className={cn("w-4 h-4", isActive ? "text-sidebar-primary-foreground" : "text-sidebar-foreground/40")} />
                    <span className="truncate flex-1 text-left">{item.name}</span>
                  </button>

                  {/* Sub-headings removed as per user request */}
                </div>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-sidebar-border flex items-center justify-between">
            <span className="text-[10px] text-sidebar-foreground/40 font-bold uppercase tracking-widest">Version</span>
            <span className="text-xs font-mono text-sidebar-foreground/60 bg-sidebar-accent px-2 py-0.5 rounded">v1.2</span>
          </div>
        </div>
      </aside>
    </>
  );
}
