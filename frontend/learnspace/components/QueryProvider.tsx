"use client";

import { ReactNode, useState } from "react";
import {
	QueryClient,
	QueryClientProvider,
	MutationCache,
	QueryCache,
} from "@tanstack/react-query";
import { useInitializeUser } from "@/hooks/useInitializeUser";

interface Props {
	children: ReactNode;
}

/**
 * Inner component that uses the hook to initialize user
 * Must be inside QueryClientProvider
 */
function UserInitializer({ children }: Props) {
	useInitializeUser(); // Automatically call /api/auth/me when user logs in
	return <>{children}</>;
}

/**
 * Central React Query provider wrapping the application.
 * - Creates a singleton QueryClient per session
 * - Enables retry + error boundary hooks if needed
 * - Automatically initializes user profile in backend
 */
export default function QueryProvider({ children }: Props) {
	const [client] = useState(
		() =>
			new QueryClient({
				queryCache: new QueryCache(),
				mutationCache: new MutationCache(),
				defaultOptions: {
					queries: {
						staleTime: 1000 * 60, // 1 min
						gcTime: 1000 * 60 * 5, // 5 min
						retry: 1,
						refetchOnWindowFocus: false,
					},
				},
			}),
	);

	return (
		<QueryClientProvider client={client}>
			<UserInitializer>{children}</UserInitializer>
		</QueryClientProvider>
	);
}
