"use client";

import { useEffect, useRef } from "react";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useInfiniteQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import ShortResponseCard from "@/components/cards/ShortResponseCard";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface Question {
	id: string;
	topic: string;
	question: string;
}

interface GenerateQuestionsResponse {
	message: string;
	num_questions: number;
	questions: Question[];
}

type QuestionsPage = {
	questions: Question[];
	count: number;
};

export default function StudyPage() {
	const { user, isLoading: authLoading } = useUser();
	const observerRef = useRef<IntersectionObserver | null>(null);
	const loadMoreRef = useRef<HTMLDivElement>(null);

	const INITIAL_BATCH_SIZE = 3;
	const LOAD_MORE_BATCH_SIZE = 3;

	const getAccessToken = async (): Promise<string> => {
		const res = await fetch("/api/auth/token");
		if (!res.ok) throw new Error("Authentication required");
		const data = await res.json();
		if (!data.accessToken) throw new Error("Authentication required");
		return data.accessToken;
	};

	const fetchQuestions = async (numQuestions: number): Promise<Question[]> => {
		const token = await getAccessToken();
		const response = await apiClient.post<GenerateQuestionsResponse>(
			"/generate-questions",
			{ num_questions: numQuestions },
			{ headers: { Authorization: `Bearer ${token}` } }
		);
		return response.data.questions;
	};

	const {
		data,
		error,
		fetchNextPage,
		hasNextPage,
		isFetchingNextPage,
		isLoading,
		isError,
	} = useInfiniteQuery({
		queryKey: ["study-questions"],
		queryFn: async ({ pageParam = INITIAL_BATCH_SIZE }) => {
			const questions = await fetchQuestions(pageParam as number);
			return { questions, count: questions.length };
		},
		initialPageParam: INITIAL_BATCH_SIZE,
		getNextPageParam: (lastPage) => {
			if (!lastPage || lastPage.count < LOAD_MORE_BATCH_SIZE) return undefined;
			return LOAD_MORE_BATCH_SIZE;
		},
		enabled: !!user,
	});

	useEffect(() => {
		if (!loadMoreRef.current || !hasNextPage || isFetchingNextPage) return;
		
		observerRef.current = new IntersectionObserver(
			(entries) => {
				if (entries[0].isIntersecting) {
					fetchNextPage();
				}
			},
			{ rootMargin: "200px", threshold: 0.1 }
		);

		const node = loadMoreRef.current;
		observerRef.current.observe(node);
		
		return () => observerRef.current?.disconnect();
	}, [hasNextPage, isFetchingNextPage, fetchNextPage]);

	const flatQuestions: Question[] = data?.pages.flatMap((page) => page.questions) || [];

	if (authLoading) {
		return (
			<div className="flex items-center justify-center min-h-[400px]">
				<Loader2 className="h-12 w-12 animate-spin text-primary" />
			</div>
		);
	}

	if (!user) return null;

	if (isLoading) {
		return (
			<div className="max-w-2xl mx-auto px-4 w-full">
				<div className="flex items-center justify-center min-h-[400px]">
					<div className="text-center">
						<Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
						<p className="text-muted-foreground">
							Generating your first questions...
						</p>
					</div>
				</div>
			</div>
		);
	}

	if (isError && flatQuestions.length === 0) {
		return (
			<div className="max-w-2xl mx-auto px-4 w-full">
				<Alert variant="destructive" className="my-8">
					<AlertCircle className="h-4 w-4" />
					<AlertTitle>Error Loading Questions</AlertTitle>
					<AlertDescription>
						{error instanceof Error ? error.message : "Failed to load questions"}
					</AlertDescription>
				</Alert>
			</div>
		);
	}

	return (
		<div className="max-w-2xl mx-auto px-4 w-full pb-20">
			<div className="mb-6">
				<h2 className="text-2xl font-bold text-foreground">
					Study Questions
				</h2>
				<p className="text-muted-foreground text-sm mt-1">
					{flatQuestions.length} question{flatQuestions.length !== 1 ? "s" : ""} loaded
					{hasNextPage && " · Scroll for more"}
				</p>
			</div>

			<div className="space-y-4">
				{flatQuestions.map((question) => (
					<ShortResponseCard
						key={question.id}
						id={question.id}
						topic={question.topic}
						question={question.question}
					/>
				))}
			</div>

			{isFetchingNextPage && (
				<div className="flex items-center justify-center py-8">
					<Loader2 className="h-8 w-8 animate-spin text-primary mr-3" />
					<span className="text-muted-foreground">Loading more...</span>
				</div>
			)}

			<div ref={loadMoreRef} className="h-10" />

			{!hasNextPage && flatQuestions.length > 0 && (
				<div className="text-center py-8">
					<p className="text-muted-foreground">🎉 You&apos;ve reached the end!</p>
				</div>
			)}

			{!isLoading && !isError && flatQuestions.length === 0 && (
				<div className="text-center py-12">
					<p className="text-muted-foreground">No questions generated</p>
				</div>
			)}
		</div>
	);
}
