"use client";

import { useEffect, useRef, useState } from "react";
import axios, { AxiosError } from "axios";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useInfiniteQuery, QueryFunctionContext } from "@tanstack/react-query";
import ShortResponseCard from "@/components/cards/ShortResponseCard";
import { Loader2, AlertCircle, Search } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

/**
 * TypeScript interfaces matching the new backend API response
 */
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

/**
 * InfiniteScrollQuestions Component (Axios Version)
 *
 * Implements infinite scroll for loading topic-based questions.
 */
export default function InfiniteScrollQuestionsAxios() {
	const { user } = useUser();
	const [topic, setTopic] = useState("");
	const [submittedTopic, setSubmittedTopic] = useState("");

	const observerRef = useRef<IntersectionObserver | null>(null);
	const loadMoreRef = useRef<HTMLDivElement>(null);

	const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
	const INITIAL_BATCH_SIZE = 5;
	const LOAD_MORE_BATCH_SIZE = 3;

	const apiClient = axios.create({
		baseURL: API_URL,
		headers: { "Content-Type": "application/json" },
		withCredentials: false,
		timeout: 30000,
	});

	useEffect(() => {
		const responseInterceptor = apiClient.interceptors.response.use(
			(response) => {
				if (process.env.NODE_ENV === "development") {
					console.log("✅ Axios Response:", response.config.url, response.data);
				}
				return response;
			},
			(error: AxiosError) => {
				if (process.env.NODE_ENV === "development") {
					console.error("❌ Axios Error:", error.config?.url, error.message);
				}
				return Promise.reject(error);
			},
		);
		return () => {
			apiClient.interceptors.response.eject(responseInterceptor);
		};
	}, [apiClient.interceptors.response]);

	const getAccessToken = async (): Promise<string> => {
		const res = await fetch("/api/auth/token");
		if (!res.ok) throw new Error("Not authenticated. Please log in to continue.");
		const data = await res.json();
		if (!data.accessToken) throw new Error("Not authenticated. Please log in to continue.");
		return data.accessToken as string;
	};

	const fetchQuestions = async (
		topic: string,
		numQuestions: number,
	): Promise<Question[]> => {
		try {
			console.log(`📤 [Axios] Fetching ${numQuestions} questions for topic "${topic}"...`);
			const token = await getAccessToken();
			const response = await apiClient.post<GenerateQuestionsResponse>(
				"/generate-questions",
				{ topic, num_questions: numQuestions },
				{ headers: { Authorization: `Bearer ${token}` } },
			);
			const { questions: newQuestions } = response.data;
			console.log(`✅ [Axios] Received ${newQuestions.length} questions.`);
			return newQuestions;
		} catch (err) {
			if (axios.isAxiosError(err)) {
				const axiosError = err as AxiosError<{ detail?: string; message?: string }>;
				const errorMessage =
					axiosError.response?.data?.detail ||
					axiosError.response?.data?.message ||
					axiosError.message;

				if (axiosError.response?.status === 401) {
					throw new Error("Authentication failed. Please log in again.");
				}
				throw new Error(`Failed to fetch questions: ${errorMessage}`);
			}
			const message = err instanceof Error ? err.message : "An unknown error occurred";
			console.error("❌ [Axios] Error fetching questions:", message);
			throw new Error(message);
		}
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
		queryKey: ["questions", submittedTopic] as const,
		queryFn: async ({ pageParam }) => {
			const size = pageParam ?? INITIAL_BATCH_SIZE;
			const q = await fetchQuestions(submittedTopic, size);
			return { questions: q, count: q.length };
		},
		initialPageParam: INITIAL_BATCH_SIZE as number,
		getNextPageParam: (lastPage) => {
			if (!lastPage || lastPage.count < LOAD_MORE_BATCH_SIZE) return undefined;
			return LOAD_MORE_BATCH_SIZE;
		},
		enabled: !!submittedTopic, // Only run query if a topic has been submitted
	});

	const handleTopicSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		if (topic.trim()) {
			setSubmittedTopic(topic.trim());
		}
	};

	const loadMoreQuestions = () => {
		if (isFetchingNextPage || !hasNextPage) return;
		fetchNextPage();
	};

	useEffect(() => {
		if (!loadMoreRef.current) return;
		observerRef.current = new IntersectionObserver(
			(entries) => {
				if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
					loadMoreQuestions();
				}
			},
			{ rootMargin: "200px", threshold: 0.1 },
		);
		const node = loadMoreRef.current;
		if (node) observerRef.current.observe(node);
		return () => observerRef.current?.disconnect();
	}, [hasNextPage, isFetchingNextPage]);

	const flatQuestions: Question[] = data?.pages.flatMap((page) => page.questions) || [];

	if (!submittedTopic) {
		return (
			<div className="max-w-2xl mx-auto px-4 w-full text-center py-20">
				<h2 className="text-2xl font-bold text-foreground mb-4">
					What do you want to learn about?
				</h2>
				<p className="text-muted-foreground mb-6">
					Enter a topic to generate practice questions.
				</p>
				<form onSubmit={handleTopicSubmit} className="flex gap-2 max-w-md mx-auto">
					<Input
						type="text"
						value={topic}
						onChange={(e) => setTopic(e.target.value)}
						placeholder="e.g., 'Python decorators' or 'WWII history'"
						className="flex-grow"
					/>
					<Button type="submit" disabled={!topic.trim()}>
						<Search className="h-4 w-4 mr-2" />
						Generate
					</Button>
				</form>
			</div>
		);
	}

	if (isLoading) {
		return (
			<div className="max-w-2xl mx-auto px-4 w-full">
				<div className="flex items-center justify-center min-h-[400px]">
					<div className="text-center">
						<Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
						<p className="text-muted-foreground">
							Generating questions for &quot;{submittedTopic}&quot;...
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
					<AlertDescription>{error.message}</AlertDescription>
				</Alert>
				<Button onClick={() => setSubmittedTopic("")} variant="outline">
					Try a different topic
				</Button>
			</div>
		);
	}

	return (
		<div className="max-w-2xl mx-auto px-4 w-full pb-20">
			<div className="mb-6">
				<h2 className="text-2xl font-bold text-foreground">
					Practice Questions for &quot;{submittedTopic}&quot;
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

			{isError && flatQuestions.length > 0 && (
				<Alert variant="destructive" className="mt-4">
					<AlertCircle className="h-4 w-4" />
					<AlertTitle>Couldn&apos;t load more</AlertTitle>
					<AlertDescription>{error.message}</AlertDescription>
				</Alert>
			)}

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
					<p className="text-xs text-muted-foreground mt-2">
						No more questions available for this topic.
					</p>
					<Button onClick={() => setSubmittedTopic("")} variant="link" className="mt-2">
						Try another topic
					</Button>
				</div>
			)}

			{!isLoading && !isError && flatQuestions.length === 0 && (
				<div className="text-center py-12">
					<p className="text-muted-foreground">
						No questions could be generated for this topic.
					</p>
					<Button onClick={() => setSubmittedTopic("")} variant="outline" className="mt-4">
						Try another topic
					</Button>
				</div>
			)}
		</div>
	);
}
