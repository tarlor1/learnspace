"use client";

import { useUser } from "@auth0/nextjs-auth0/client";
import { useQuery } from "@tanstack/react-query";
import {
	UserIcon,
	Mail,
	Calendar,
	BarChart3,
	History,
	CheckCircle,
	XCircle,
	Target,
	Flame,
} from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";

interface UserStats {
	total_answers: number;
	correct_answers: number;
	accuracy: number;
	average_score: number;
	recent_activity_7d: number;
	streak_days: number;
	member_since: string;
}

interface RecentAnswer {
	id: string;
	question_id: string;
	question_topic: string;
	user_answer: string;
	was_correct: boolean;
	answer_score: number;
	answered_at: string;
	is_good_question: boolean | null;
}

export default function ProfilePage() {
	const { user, isLoading: authLoading } = useUser();

	const getAccessToken = async (): Promise<string> => {
		const res = await fetch("/api/auth/token");
		if (!res.ok) throw new Error("Authentication required");
		const data = await res.json();
		if (!data.accessToken) throw new Error("Authentication required");
		return data.accessToken;
	};

	const { data: stats, isLoading: statsLoading } = useQuery<UserStats>({
		queryKey: ["user-stats"],
		queryFn: async () => {
			const token = await getAccessToken();
			const response = await apiClient.get<UserStats>("/profile/stats", {
				headers: { Authorization: `Bearer ${token}` },
			});
			return response.data;
		},
		enabled: !!user,
	});

	const { data: recentAnswers, isLoading: answersLoading } = useQuery<
		RecentAnswer[]
	>({
		queryKey: ["recent-answers"],
		queryFn: async () => {
			const token = await getAccessToken();
			const response = await apiClient.get<RecentAnswer[]>(
				"/profile/recent-answers?limit=10",
				{
					headers: { Authorization: `Bearer ${token}` },
				},
			);
			return response.data;
		},
		enabled: !!user,
	});

	if (authLoading) {
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
		<div className="max-w-4xl mx-auto px-4 w-full pb-20">
			<div className="mb-8">
				<h2 className="text-2xl font-bold text-foreground">My Profile</h2>
				<p className="text-muted-foreground text-sm mt-1">
					View your account information and learning progress
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
							<Calendar className="w-5 h-5 text-primary mt-0.5 shrink-0" />
							<div>
								<p className="text-sm text-muted-foreground mb-1">
									Member Since
								</p>
								<p className="font-semibold text-foreground">
									{stats?.member_since
										? new Date(stats.member_since).toLocaleDateString()
										: user.updated_at
										? new Date(user.updated_at).toLocaleDateString()
										: "Recently"}
								</p>
							</div>
						</div>
						<div className="flex items-start gap-3">
							<Mail className="w-5 h-5 text-primary mt-0.5 shrink-0" />
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

			{/* Tabs for Statistics and Activity */}
			<Tabs defaultValue="statistics" className="w-full">
				<TabsList className="grid w-full grid-cols-2">
					<TabsTrigger value="statistics">
						<BarChart3 className="w-4 h-4 mr-2" />
						Statistics
					</TabsTrigger>
					<TabsTrigger value="activity">
						<History className="w-4 h-4 mr-2" />
						Recent Activity
					</TabsTrigger>
				</TabsList>

				{/* Statistics Tab */}
				<TabsContent value="statistics">
					{statsLoading ? (
						<Card>
							<CardContent className="pt-6">
								<div className="flex items-center justify-center py-8">
									<Loader2 className="h-8 w-8 animate-spin text-primary mr-3" />
									<span className="text-muted-foreground">
										Loading statistics...
									</span>
								</div>
							</CardContent>
						</Card>
					) : (
						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<BarChart3 className="w-5 h-5" />
									Your Learning Statistics
								</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									<div className="p-4 rounded-lg bg-muted/30">
										<div className="flex items-center gap-2 mb-1">
											<Target className="w-5 h-5 text-primary" />
											<p className="text-sm text-muted-foreground">
												Total Questions Answered
											</p>
										</div>
										<p className="text-3xl font-bold text-primary">
											{stats?.total_answers || 0}
										</p>
										{stats && stats.total_answers === 0 && (
											<p className="text-xs text-muted-foreground mt-2">
												Start studying to track your progress! 🎯
											</p>
										)}
									</div>

									<div className="grid grid-cols-2 gap-4">
										<div className="p-4 rounded-lg bg-muted/30">
											<div className="flex items-center gap-2 mb-2">
												<Flame className="w-5 h-5 text-orange-500" />
												<p className="text-sm text-muted-foreground">Streak</p>
											</div>
											<p className="text-2xl font-bold text-primary">
												{stats?.streak_days || 0} days
											</p>
										</div>
										<div className="p-4 rounded-lg bg-muted/30">
											<div className="flex items-center gap-2 mb-2">
												<CheckCircle className="w-5 h-5 text-green-500" />
												<p className="text-sm text-muted-foreground">
													Accuracy
												</p>
											</div>
											<p className="text-2xl font-bold text-primary">
												{stats?.accuracy || 0}%
											</p>
										</div>
									</div>

									<div className="grid grid-cols-2 gap-4">
										<div className="p-4 rounded-lg bg-muted/30">
											<p className="text-sm text-muted-foreground mb-2">
												Correct Answers
											</p>
											<p className="text-2xl font-bold text-green-600">
												{stats?.correct_answers || 0}
											</p>
										</div>
										<div className="p-4 rounded-lg bg-muted/30">
											<p className="text-sm text-muted-foreground mb-2">
												Average Score
											</p>
											<p className="text-2xl font-bold text-primary">
												{stats?.average_score || 0}%
											</p>
										</div>
									</div>

									<div className="p-4 rounded-lg bg-muted/30">
										<p className="text-sm text-muted-foreground mb-2">
											Last 7 Days Activity
										</p>
										<p className="text-2xl font-bold text-primary">
											{stats?.recent_activity_7d || 0} questions
										</p>
									</div>
								</div>
							</CardContent>
						</Card>
					)}
				</TabsContent>

				{/* Recent Activity Tab */}
				<TabsContent value="activity">
					{answersLoading ? (
						<Card>
							<CardContent className="pt-6">
								<div className="flex items-center justify-center py-8">
									<Loader2 className="h-8 w-8 animate-spin text-primary mr-3" />
									<span className="text-muted-foreground">
										Loading activity...
									</span>
								</div>
							</CardContent>
						</Card>
					) : (
						<Card>
							<CardHeader>
								<CardTitle className="flex items-center gap-2">
									<History className="w-5 h-5" />
									Recent Answers
								</CardTitle>
								<CardDescription>
									Your last 10 answered questions
								</CardDescription>
							</CardHeader>
							<CardContent>
								{recentAnswers && recentAnswers.length > 0 ? (
									<div className="space-y-4">
										{recentAnswers.map((answer) => (
											<div
												key={answer.id}
												className="p-4 rounded-lg border border-border bg-card hover:bg-muted/30 transition-colors"
											>
												<div className="flex items-start justify-between gap-4 mb-2">
													<div className="flex-1">
														<div className="flex items-center gap-2 mb-1">
															<Badge variant="secondary" className="text-xs">
																{answer.question_topic}
															</Badge>
															{answer.was_correct ? (
																<CheckCircle className="w-4 h-4 text-green-500" />
															) : (
																<XCircle className="w-4 h-4 text-red-500" />
															)}
														</div>
														<p className="text-sm text-muted-foreground line-clamp-2">
															{answer.user_answer}
														</p>
													</div>
													<div className="text-right shrink-0">
														<p className="text-lg font-bold text-primary">
															{answer.answer_score}%
														</p>
														<p className="text-xs text-muted-foreground">
															{new Date(
																answer.answered_at,
															).toLocaleDateString()}
														</p>
													</div>
												</div>
											</div>
										))}
									</div>
								) : (
									<div className="text-center py-12">
										<History className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
										<p className="text-muted-foreground">
											No answers yet. Start studying to see your activity!
										</p>
									</div>
								)}
							</CardContent>
						</Card>
					)}
				</TabsContent>
			</Tabs>
		</div>
	);
}
