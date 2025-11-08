"use client";

import { useUser } from "@auth0/nextjs-auth0/client";
import { UserIcon, Mail, Calendar, BarChart3 } from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";

export default function ProfilePage() {
	const { user, isLoading } = useUser();

	if (isLoading) {
		return (
			<div className="max-w-2xl mx-auto px-4 w-full">
				<div className="flex items-center justify-center min-h-[400px]">
					<div className="text-center">
						<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
						<p className="text-muted-foreground">Loading profile...</p>
					</div>
				</div>
			</div>
		);
	}

	if (!user) {
		return null; // Middleware will redirect
	}
	return (
		<div className="max-w-2xl mx-auto px-4 w-full">
			<div className="mb-8">
				<h2 className="text-2xl font-bold text-foreground">My Profile</h2>
				<p className="text-muted-foreground text-sm mt-1">
					View your account information
				</p>
			</div>

			{/* Profile Card */}
			<Card className="mb-8">
				<CardHeader className="bg-muted/30">
					<div className="flex items-start gap-4">
						<div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center">
							<UserIcon className="w-8 h-8 text-primary-foreground" />
						</div>
						<div className="flex-1">
							<CardTitle className="text-2xl">{user.name}</CardTitle>
							<CardDescription>{user.email}</CardDescription>
						</div>
					</div>
				</CardHeader>
				<CardContent className="pt-6">
					<div className="grid grid-cols-2 gap-4">
						<div className="flex items-start gap-3">
							<Calendar className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
							<div>
								<p className="text-sm text-muted-foreground mb-1">
									Member Since
								</p>
								<p className="font-semibold text-foreground">
									{new Date(user.updated_at || Date.now()).toLocaleDateString()}
								</p>
							</div>
						</div>
						<div className="flex items-start gap-3">
							<Mail className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
							<div>
								<p className="text-sm text-muted-foreground mb-2">Email</p>
								<p className="font-semibold text-foreground text-sm break-all">
									{user.email}
								</p>
							</div>
						</div>
					</div>
				</CardContent>
			</Card>

			{/* Statistics */}
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<BarChart3 className="w-5 h-5" />
						Your Statistics
					</CardTitle>
				</CardHeader>
				<CardContent>
					<div className="space-y-4">
						<div className="p-4 rounded-lg bg-muted/30">
							<p className="text-sm text-muted-foreground mb-1">
								Total Cards Completed
							</p>
							<p className="text-3xl font-bold text-primary">0</p>
							<p className="text-xs text-muted-foreground mt-2">
								Start studying to track your progress! 🎯
							</p>
						</div>

						<div className="grid grid-cols-2 gap-4">
							<div className="p-4 rounded-lg bg-muted/30">
								<p className="text-sm text-muted-foreground mb-2">Streak</p>
								<p className="text-2xl font-bold text-primary">7 days</p>
							</div>
							<div className="p-4 rounded-lg bg-muted/30">
								<p className="text-sm text-muted-foreground mb-2">Accuracy</p>
								<p className="text-2xl font-bold text-primary">85%</p>
							</div>
						</div>
					</div>
				</CardContent>
			</Card>
		</div>
	);
}
