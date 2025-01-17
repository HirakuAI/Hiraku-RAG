import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { Textarea } from "@/components/ui/textarea";

export const GlowingTextarea = forwardRef<
  HTMLTextAreaElement,
  React.ComponentPropsWithoutRef<typeof Textarea> & { isProcessing?: boolean }
>(({ className, isProcessing, ...props }, ref) => {
  return (
    <div
      className={cn(
        "relative rounded-lg",
        "before:absolute before:inset-0 before:rounded-lg before:p-[1px]",
        "before:bg-gradient-to-r before:from-[#6a1b9a] before:via-[#9c27b0] before:via-[#ce93d8] before:via-[#e91e63] before:to-[#6a1b9a]",
        "before:bg-[length:400%_400%]",
        "before:animate-glow-clockwise",
        "after:absolute after:inset-[1px] after:rounded-[7px] after:bg-background",
        isProcessing && [
          "before:animate-glow-thinking",
          "shadow-[0_0_20px_rgba(156,39,176,0.7)]",
          "backdrop-blur-sm",
          "before:opacity-90",
        ],
        "shadow-[0_0_2px_rgba(156,39,176,0.2)]",
        "hover:shadow-[0_0_10px_rgba(156,39,176,0.4)]",
        "transition-all duration-300"
      )}
    >
      <Textarea
        ref={ref}
        className={cn(
          "relative z-10 border-0 bg-transparent focus-visible:ring-0",
          "rounded-lg resize-none transition-opacity duration-300",
          isProcessing && "opacity-70",
          className
        )}
        {...props}
      />
    </div>
  );
});

GlowingTextarea.displayName = "GlowingTextarea";

export default { GlowingTextarea };
