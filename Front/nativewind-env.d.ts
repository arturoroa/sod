/// <reference types="vite/client" />

declare global {
	interface Window {
		require?: (assetPath: string) => string;
	}

	var require: (assetPath: string) => string;
}

export {};