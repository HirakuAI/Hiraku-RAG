import { ModeToggle } from "./mode-toggle"

interface HeaderProps {
  title: string
}

export function Header({ title }: HeaderProps) {
  return (
    <header className="border-b">
      <div className="flex h-16 items-center px-4">
        <h1 className="text-lg font-semibold">{title}</h1>
        <div className="ml-auto flex items-center space-x-4">
          <ModeToggle />
        </div>
      </div>
    </header>
  )
}

