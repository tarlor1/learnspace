"use client";

import { ReactNode, useState } from "react";
import {
	QueryClient,
	QueryClientProvider,
	MutationCache,
	QueryCache,
} from "@tanstack/react-query";

interface Props {
	children: ReactNode;
}

/**
 * Central React Query provider wrapping the application.
 * - Creates a singleton QueryClient per session
 * - Enables retry + error boundary hooks if needed
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
			})
	);

	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
