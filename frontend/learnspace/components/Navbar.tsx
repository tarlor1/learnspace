"use client";

import { useUser } from "@auth0/nextjs-auth0/client";
import { Button } from "@/components/ui/button";
import { LogIn, LogOut, User } from "lucide-react";
import Link from "next/link";

export default function Navbar() {
	const { user, isLoading } = useUser();

	return (
		<nav className="fixed top-0 left-0 right-0 bg-card border-b border-border shadow-sm z-50">
			<div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
				<div className="flex items-center gap-2">
					<div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
						<span className="text-primary-foreground font-bold text-sm">
							LS
						</span>
					</div>
					<h1 className="text-xl font-bold text-foreground">LearnSpace</h1>
				</div>

				<div className="flex items-center gap-3">
					{!isLoading && (
						<>
							{user ? (
								<div className="flex items-center gap-3">
									<Link href="/profile">
										<Button variant="ghost" size="sm">
											<User className="w-4 h-4 mr-2" />
											Profile
										</Button>
									</Link>
									<Link href="/api/auth/logout">
										<Button variant="outline" size="sm">
											<LogOut className="w-4 h-4 mr-2" />
											Logout
										</Button>
									</Link>
								</div>
							) : (
								<Link href="/api/auth/login">
									<Button size="sm">
										<LogIn className="w-4 h-4 mr-2" />
										Login
									</Button>
								</Link>
							)}
						</>
					)}
				</div>
			</div>
		</nav>
	);
}
