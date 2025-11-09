"use client";

import { useUser } from "@auth0/nextjs-auth0/client";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

/**
 * Custom hook to initialize user profile in backend database
 * Automatically calls /api/auth/me when user is authenticated
 * This ensures the user profile exists in PostgreSQL
 */
export function useInitializeUser() {
	const { user, isLoading } = useUser();

	const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

	const getAccessToken = async (): Promise<string> => {
		const res = await fetch("/api/auth/token");
		if (!res.ok) throw new Error("Authentication required");
		const data = await res.json();
		if (!data.accessToken) throw new Error("Authentication required");
		return data.accessToken;
	};

	// Query to initialize user profile
	const { data, error } = useQuery({
		queryKey: ["user-init", user?.sub],
		queryFn: async () => {
			const token = await getAccessToken();
			const response = await fetch(`${API_URL}/api/auth/me`, {
				headers: {
					Authorization: `Bearer ${token}`,
				},
			});

			if (!response.ok) {
				throw new Error("Failed to initialize user profile");
			}

			return response.json();
		},
		enabled: !!user && !isLoading, // Only run when user is authenticated
		staleTime: Infinity, // Only need to run once per session
		retry: 1,
	});

	useEffect(() => {
		if (data) {
			console.log("✅ User profile initialized:", data.sub);
		}
		if (error) {
			console.error("❌ Failed to initialize user profile:", error);
		}
	}, [data, error]);

	return { initialized: !!data, error };
}
