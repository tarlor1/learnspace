/**
 * API client for making authenticated requests to the backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Make an authenticated API request
 * @param endpoint - API endpoint (e.g., '/generate-questions')
 * @param options - Fetch options
 * @returns Response data
 */
export async function authenticatedFetch<T = any>(
	endpoint: string,
	options: RequestInit = {},
): Promise<T> {
	// Get access token from Auth0 session
	const tokenResponse = await fetch("/api/auth/token");
	const { accessToken } = await tokenResponse.json();

	const response = await fetch(`${API_URL}${endpoint}`, {
		...options,
		headers: {
			"Content-Type": "application/json",
			...(accessToken && { Authorization: `Bearer ${accessToken}` }),
			...options.headers,
		},
	});

	if (!response.ok) {
		const error = await response
			.json()
			.catch(() => ({ message: "An error occurred" }));
		throw new Error(error.message || error.detail || "API request failed");
	}

	return response.json();
}

/**
 * Generate questions from PDF text
 */
export async function generateQuestions(
	pdfText: string,
	numQuestions: number = 10,
) {
	return authenticatedFetch("/generate-questions", {
		method: "POST",
		body: JSON.stringify({
			pdf_text: pdfText,
			num_questions: numQuestions,
		}),
	});
}

/**
 * Submit an answer to a question
 */
export async function submitAnswer(questionId: string, answer: string) {
	return authenticatedFetch("/submit-answer", {
		method: "POST",
		body: JSON.stringify({
			question_id: questionId,
			answer: answer,
		}),
	});
}

/**
 * Get all questions
 */
export async function getQuestions() {
	return authenticatedFetch("/questions");
}

/**
 * Get session data
 */
export async function getSession(sessionId: string) {
	return authenticatedFetch(`/session/${sessionId}`);
}
