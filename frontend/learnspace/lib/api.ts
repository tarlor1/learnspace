import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
	baseURL: API_URL,
	headers: {
		"Content-Type": "application/json",
	},
	withCredentials: true,
	timeout: 30000,
});

async function getAccessToken(): Promise<string> {
	const tokenResponse = await fetch("/api/auth/token");
	if (!tokenResponse.ok) throw new Error("Authentication required");
	const { accessToken } = await tokenResponse.json();
	if (!accessToken) throw new Error("Authentication required");
	return accessToken;
}

export async function authenticatedFetch<T = any>(
	endpoint: string,
	options: RequestInit = {},
): Promise<T> {
	const accessToken = await getAccessToken();

	const response = await fetch(`${API_URL}${endpoint}`, {
		...options,
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${accessToken}`,
			...options.headers,
		},
	});

	if (!response.ok) {
		const error = await response
			.json()
			.catch(() => ({ message: "An error occurred" }));
		throw new Error(error.detail || error.message || "API request failed");
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
