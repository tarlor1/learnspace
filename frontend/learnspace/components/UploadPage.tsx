"use client";

import { useUser } from "@auth0/nextjs-auth0/client";
import {
	UploadIcon,
	FileText,
	Loader2,
	CheckCircle,
	XCircle,
} from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { useState, useRef, useEffect } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface Chapter {
	id: string;
	chapter_number: number;
	title: string;
	summary: string;
}

interface Document {
	id: string;
	name: string;
	status: string;
	created_at: string;
	chapter_count: number;
	chapters: Chapter[];
}

interface DocumentsResponse {
	documents: Document[];
}

export default function UploadPage() {
	const { user, isLoading: authLoading } = useUser();
	const [uploadError, setUploadError] = useState<string | null>(null);
	const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
	const fileInputRef = useRef<HTMLInputElement>(null);
	const queryClient = useQueryClient();

	const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

	const getAccessToken = async (): Promise<string> => {
		const res = await fetch("/api/auth/token");
		if (!res.ok) throw new Error("Authentication required");
		const data = await res.json();
		if (!data.accessToken) throw new Error("Authentication required");
		return data.accessToken;
	};

	// Fetch documents with React Query
	const { data: documentsData, isLoading: loadingDocs } =
		useQuery<DocumentsResponse>({
			queryKey: ["documents"],
			queryFn: async () => {
				const token = await getAccessToken();
				const response = await fetch(`${API_URL}/api/documents/`, {
					headers: {
						Authorization: `Bearer ${token}`,
					},
				});

				if (!response.ok) throw new Error("Failed to fetch documents");
				return response.json();
			},
			enabled: !!user && !authLoading, // Only fetch when user is authenticated and not loading
			refetchInterval: 5000, // Refetch every 5 seconds to catch processing updates
		});

	// Cleanup stuck documents once on mount
	useEffect(() => {
		const cleanupStuckDocuments = async () => {
			if (!user) return;

			try {
				const token = await getAccessToken();
				const response = await fetch(`${API_URL}/api/documents/cleanup-stuck`, {
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
					},
				});

				if (response.ok) {
					const data = await response.json();
					if (data.count > 0) {
						console.log(`🧹 Cleaned up ${data.count} stuck documents on mount`);
						queryClient.invalidateQueries({ queryKey: ["documents"] });
					}
				}
			} catch (error) {
				console.error("Cleanup error:", error);
			}
		};

		cleanupStuckDocuments();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [user]); // Only run when user changes (login/logout)

	// Upload mutation with React Query
	const uploadMutation = useMutation({
		mutationFn: async (file: File) => {
			const token = await getAccessToken();
			const formData = new FormData();
			formData.append("file", file);

			const response = await fetch(`${API_URL}/api/documents/upload`, {
				method: "POST",
				headers: {
					Authorization: `Bearer ${token}`,
				},
				body: formData,
			});

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.detail || "Upload failed");
			}

			return response.json();
		},
		onSuccess: (data, file) => {
			setUploadSuccess(`Successfully uploaded: ${file.name}`);
			// Invalidate and refetch documents
			queryClient.invalidateQueries({ queryKey: ["documents"] });

			// Clear file input
			if (fileInputRef.current) {
				fileInputRef.current.value = "";
			}

			// Clear success message after 5 seconds
			setTimeout(() => setUploadSuccess(null), 5000);
		},
		onError: (error: Error) => {
			console.error("Upload error:", error);
			setUploadError(error.message);
		},
	});

	const documents = documentsData?.documents || [];

	const handleFileSelect = async (
		event: React.ChangeEvent<HTMLInputElement>,
	) => {
		const file = event.target.files?.[0];
		if (!file) return;

		if (!file.name.endsWith(".pdf")) {
			setUploadError("Please upload a PDF file");
			return;
		}

		setUploadError(null);
		setUploadSuccess(null);
		uploadMutation.mutate(file);
	};

	const handleDragOver = (event: React.DragEvent) => {
		event.preventDefault();
	};

	const handleDrop = async (event: React.DragEvent) => {
		event.preventDefault();
		const file = event.dataTransfer.files?.[0];
		if (!file) return;

		if (!file.name.endsWith(".pdf")) {
			setUploadError("Please upload a PDF file");
			return;
		}

		setUploadError(null);
		setUploadSuccess(null);
		uploadMutation.mutate(file);
	};

	// Show loading state while checking auth
	if (authLoading || loadingDocs) {
		return (
			<div className="max-w-2xl mx-auto px-4 w-full">
				<div className="flex items-center justify-center min-h-[400px]">
					<div className="text-center">
						<Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
						<p className="text-muted-foreground">Loading your documents...</p>
					</div>
				</div>
			</div>
		);
	}

	// Failsafe - middleware should already handle this
	if (!user) {
		return null;
	}

	return (
		<div className="max-w-2xl mx-auto px-4 w-full">
			<div className="mb-8">
				<h2 className="text-2xl font-bold text-foreground">My Documents</h2>
				<p className="text-muted-foreground text-sm mt-1">
					Manage your uploaded documents and track progress · {user.email}
				</p>
			</div>

			{/* Success/Error Messages */}
			{uploadSuccess && (
				<Alert className="mb-4 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
					<CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
					<AlertDescription className="text-green-800 dark:text-green-200">
						{uploadSuccess}
					</AlertDescription>
				</Alert>
			)}

			{uploadError && (
				<Alert className="mb-4 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
					<XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
					<AlertDescription className="text-red-800 dark:text-red-200">
						{uploadError}
					</AlertDescription>
				</Alert>
			)}

			{/* Upload Section */}
			<Card className="mb-8 border-2 border-dashed">
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<UploadIcon className="w-5 h-5" />
						Upload New Document
					</CardTitle>
					<CardDescription>
						Drag and drop your PDF or click to browse
					</CardDescription>
				</CardHeader>
				<CardContent>
					<input
						ref={fileInputRef}
						type="file"
						accept=".pdf"
						onChange={handleFileSelect}
						className="hidden"
						disabled={uploadMutation.isPending}
					/>
					<div
						onClick={() =>
							!uploadMutation.isPending && fileInputRef.current?.click()
						}
						onDragOver={handleDragOver}
						onDrop={handleDrop}
						className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer"
					>
						{uploadMutation.isPending ? (
							<>
								<Loader2 className="w-12 h-12 text-primary mx-auto mb-3 animate-spin" />
								<p className="font-medium text-foreground mb-1">
									Processing document...
								</p>
								<p className="text-sm text-muted-foreground">
									This may take a minute
								</p>
							</>
						) : (
							<>
								<UploadIcon className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
								<p className="font-medium text-foreground mb-1">
									Drop your PDF here
								</p>
								<p className="text-sm text-muted-foreground">
									or click to select a file
								</p>
							</>
						)}
					</div>
				</CardContent>
			</Card>

			{/* Documents List */}
			<div className="space-y-4">
				<h3 className="font-semibold text-foreground">
					Your Documents ({documents.length})
				</h3>

				{documents.length === 0 ? (
					<Card>
						<CardContent className="py-12 text-center">
							<FileText className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
							<p className="text-muted-foreground mb-1">No documents yet</p>
							<p className="text-sm text-muted-foreground">
								Upload your first PDF to get started
							</p>
						</CardContent>
					</Card>
				) : (
					documents.map((doc) => {
						const uploadDate = new Date(doc.created_at).toLocaleDateString();
						const isProcessing = doc.status === "processing";
						const isError = doc.status === "error";
						const isReady = doc.status === "ready";

						return (
							<Card key={doc.id} className="overflow-hidden">
								<CardHeader className="pb-3">
									<div className="flex items-start justify-between">
										<div className="flex-1">
											<div className="flex items-center gap-2 mb-2">
												<FileText className="w-4 h-4 text-primary" />
												<CardTitle className="text-lg">{doc.name}</CardTitle>
											</div>
											<CardDescription>
												Uploaded {uploadDate} · {doc.chapter_count} chapters
											</CardDescription>
										</div>
										<div className="flex items-center gap-2">
											{isProcessing && (
												<div className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400">
													<Loader2 className="w-4 h-4 animate-spin" />
													<span>Processing...</span>
												</div>
											)}
											{isReady && (
												<div className="flex items-center gap-1 text-sm text-green-600 dark:text-green-400">
													<CheckCircle className="w-4 h-4" />
													<span>Ready</span>
												</div>
											)}
											{isError && (
												<div className="flex items-center gap-1 text-sm text-red-600 dark:text-red-400">
													<XCircle className="w-4 h-4" />
													<span>Error</span>
												</div>
											)}
										</div>
									</div>
								</CardHeader>

								{/* Chapter List */}
								{isReady && doc.chapters && doc.chapters.length > 0 && (
									<CardContent className="pt-0">
										<div className="space-y-2">
											<p className="text-sm font-medium text-muted-foreground mb-3">
												Chapters:
											</p>
											{doc.chapters.map((chapter) => (
												<div
													key={chapter.id}
													className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
												>
													<div className="flex items-start gap-3">
														<div className="shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm">
															{chapter.chapter_number}
														</div>
														<div className="flex-1 min-w-0">
															<h4 className="font-medium text-sm text-foreground mb-1">
																{chapter.title}
															</h4>
															<p className="text-xs text-muted-foreground line-clamp-2">
																{chapter.summary}
															</p>
														</div>
													</div>
												</div>
											))}
										</div>
									</CardContent>
								)}
							</Card>
						);
					})
				)}
			</div>
		</div>
	);
}
