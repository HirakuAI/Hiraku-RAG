'use client'

import { useState } from "react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/use-toast"
import { useAuth } from "@/lib/auth-context"

interface LoginFormProps extends React.ComponentPropsWithoutRef<"div"> {}

export function LoginForm({ className, ...props }: LoginFormProps) {
  const router = useRouter()
  const [isRegistering, setIsRegistering] = useState(false)
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
  })
  const { toast } = useToast()
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const endpoint = isRegistering ? '/api/register' : '/api/login'
    const payload = isRegistering 
      ? { email: formData.email, username: formData.username, password: formData.password }
      : { username: formData.username, password: formData.password }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Authentication failed')
      }

      if (isRegistering) {
        toast({
          title: "Registration Successful",
          description: "Please login with your credentials",
        })
        setIsRegistering(false)
      } else {
        // Use auth context to store user data from API response
        login(data.token, {
          username: data.user.username,
          email: data.user.email
        })
        toast({
          title: "Login Successful",
          description: "Welcome back!",
        })
        // Redirect to main page after successful login
        router.push('/')
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Authentication failed",
        variant: "destructive",
      })
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">{isRegistering ? 'Register' : 'Login'}</CardTitle>
          <CardDescription>
            {isRegistering 
              ? 'Create a new account'
              : 'Enter your credentials to login to your account'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              {isRegistering && (
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
              )}
              <div className="grid gap-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="username"
                  value={formData.username}
                  onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                  required
                />
              </div>
              <div className="grid gap-2">
                <div className="flex items-center">
                  <Label htmlFor="password">Password</Label>
                  {!isRegistering && (
                    <a
                      href="#"
                      className="ml-auto inline-block text-sm underline-offset-4 hover:underline"
                      onClick={(e) => {
                        e.preventDefault()
                        toast({
                          title: "Not Implemented",
                          description: "Password reset functionality is not available yet.",
                        })
                      }}
                    >
                      Forgot your password?
                    </a>
                  )}
                </div>
                <Input 
                  id="password" 
                  type="password" 
                  value={formData.password}
                  onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                  required 
                />
              </div>
              <Button type="submit" className="w-full">
                {isRegistering ? 'Register' : 'Login'}
              </Button>
            </div>
            <div className="mt-4 text-center text-sm">
              {isRegistering ? (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => setIsRegistering(false)}
                    className="underline underline-offset-4"
                  >
                    Login
                  </button>
                </>
              ) : (
                <>
                  Don&apos;t have an account?{" "}
                  <button
                    type="button"
                    onClick={() => setIsRegistering(true)}
                    className="underline underline-offset-4"
                  >
                    Sign up
                  </button>
                </>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
