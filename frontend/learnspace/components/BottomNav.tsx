"use client";

import { BookOpen, Upload, User } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export default function BottomNav() {
	const pathname = usePathname();

	const navItems = [
		{ id: "study", label: "Study", icon: BookOpen, href: "/study" },
		{ id: "upload", label: "Upload", icon: Upload, href: "/upload" },
		{ id: "profile", label: "Profile", icon: User, href: "/profile" },
	] as const;

	return (
		<nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border shadow-lg z-50">
			<div className="max-w-4xl mx-auto px-4">
				<div className="flex items-center justify-around h-16">
					{navItems.map((item) => {
						const Icon = item.icon;
						const isActive = pathname === item.href;
						return (
							<Link
								key={item.id}
								href={item.href}
								className={cn(
									"flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors",
									isActive
										? "text-primary border-t-2 border-primary"
										: "text-muted-foreground hover:text-foreground",
								)}
							>
								<Icon className="w-5 h-5" />
								<span className="text-xs font-medium">{item.label}</span>
							</Link>
						);
					})}
				</div>
			</div>
		</nav>
	);
}
