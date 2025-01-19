import React, { useState, useEffect, useCallback } from "react";
import { FileText, File, X, Check, AlertCircle, Download } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface FileMetadata {
  id: string;
  name: string;
  type: string;
  size: number;
  created_at: string;
  modified_at: string;
}

interface FileManagementPanelProps {
  className?: string;
}

export default function FileManagementPanel({
  className,
}: FileManagementPanelProps) {
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [fileToDelete, setFileToDelete] = useState<FileMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const fetchFiles = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;

      try {
        // Fetch both files and active status in one call
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/files`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) throw new Error("Failed to fetch files");

        const data = await response.json();
        setFiles(data.files);
        setSelectedFiles(new Set(data.activeFiles));
        setIsInitialized(true);
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to load files",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchFiles();
  }, []);

  useEffect(() => {
    if (isInitialized) {
      localStorage.setItem(
        "selectedFiles",
        JSON.stringify(Array.from(selectedFiles))
      );
    }
  }, [selectedFiles, isInitialized]);

  const toggleFile = (fileId: string) => {
    setSelectedFiles((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(fileId)) {
        newSet.delete(fileId);
      } else {
        newSet.add(fileId);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(files.map((file) => String(file.id))));
    }
  };

  const handleDelete = async (file: FileMetadata) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Authentication required");

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/files/${file.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete file");
      }

      setFiles((prev) => prev.filter((f) => f.id !== file.id));
      setSelectedFiles((prev) => {
        const newSet = new Set(prev);
        newSet.delete(String(file.id));
        return newSet;
      });

      const savedSelection = localStorage.getItem("selectedFiles");
      if (savedSelection) {
        const selectedSet = new Set(JSON.parse(savedSelection));
        selectedSet.delete(String(file.id));
        localStorage.setItem(
          "selectedFiles",
          JSON.stringify(Array.from(selectedSet))
        );
      }

      toast({
        title: "Success",
        description: "File deleted successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to delete file",
        variant: "destructive",
      });
    }
    setFileToDelete(null);
  };

  const getFileIcon = (type: string) => {
    if (type.includes("pdf")) return <FileText className="h-4 w-4" />;
    return <File className="h-4 w-4" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-sm text-muted-foreground">Loading files...</span>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium">Knowledge Base</h3>
        <Button variant="ghost" size="sm" onClick={toggleSelectAll}>
          {selectedFiles.size === files.length ? "Deselect All" : "Select All"}
        </Button>
      </div>

      <ScrollArea className="h-[calc(100vh-20rem)]">
        <div className="space-y-2 pr-4">
          {files.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No files uploaded yet
            </div>
          ) : (
            files.map((file) => (
              <div
                key={file.id}
                className={`
                  group relative flex items-center gap-2 p-2 rounded-lg border 
                  transition-colors cursor-pointer
                  ${
                    selectedFiles.has(String(file.id))
                      ? "bg-primary/5 border-primary"
                      : "hover:bg-accent"
                  }
                `}
                onClick={() => toggleFile(String(file.id))}
              >
                {getFileIcon(file.type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <div className="flex items-center gap-2">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={(e) => {
                                e.stopPropagation();
                                setFileToDelete(file);
                              }}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Remove file</TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      <div
                        className={`
                        h-4 w-4 rounded-full flex items-center justify-center
                        transition-colors
                        ${
                          selectedFiles.has(String(file.id))
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        }
                      `}
                      >
                        <Check className="h-3 w-3" />
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                    <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                    <span>•</span>
                    <span>
                      {formatDistanceToNow(new Date(file.modified_at))} ago
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      <AlertDialog
        open={!!fileToDelete}
        onOpenChange={() => setFileToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Delete File
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{fileToDelete?.name}"? This will
              remove it from the knowledge base.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => fileToDelete && handleDelete(fileToDelete)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
