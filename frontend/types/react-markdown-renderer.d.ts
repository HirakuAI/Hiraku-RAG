declare module 'react-markdown-renderer' {
  import { ComponentType } from 'react';
  
  interface MarkdownRendererProps {
    markdown: string;
  }
  
  const MarkdownRenderer: ComponentType<MarkdownRendererProps>;
  export default MarkdownRenderer;
} 