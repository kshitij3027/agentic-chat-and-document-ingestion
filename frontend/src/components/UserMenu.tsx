import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, Settings } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'

interface UserMenuProps {
  email: string
  onSignOut: () => void
  isAdmin?: boolean
}

function getInitials(email: string): string {
  const name = email.split('@')[0]
  const parts = name.split(/[._-]/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
}

function getDisplayName(email: string): string {
  const name = email.split('@')[0]
  return name
    .split(/[._-]/)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function getAvatarColor(email: string): string {
  const colors = [
    'bg-orange-500',
    'bg-blue-500',
    'bg-green-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-yellow-500',
    'bg-red-500',
    'bg-indigo-500',
  ]
  let hash = 0
  for (let i = 0; i < email.length; i++) {
    hash = email.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

export function UserMenu({ email, onSignOut, isAdmin = false }: UserMenuProps) {
  const [popoverOpen, setPopoverOpen] = useState(false)
  const navigate = useNavigate()

  const initials = getInitials(email)
  const displayName = getDisplayName(email)
  const avatarColor = getAvatarColor(email)

  function handleOpenSettings() {
    setPopoverOpen(false)
    navigate('/settings')
  }

  return (
    <>
      <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
        <PopoverTrigger asChild>
          <button className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-accent transition-colors">
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${avatarColor} text-white text-sm font-medium`}>
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{displayName}</p>
              <p className="truncate text-xs text-muted-foreground">{email}</p>
            </div>
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-56 p-2" align="start" side="top">
          {isAdmin && (
            <Button
              variant="ghost"
              className="w-full justify-start gap-2"
              onClick={handleOpenSettings}
            >
              <Settings className="h-4 w-4" />
              Settings
            </Button>
          )}
          <Button
            variant="ghost"
            className="w-full justify-start gap-2"
            onClick={onSignOut}
          >
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </PopoverContent>
      </Popover>
    </>
  )
}
