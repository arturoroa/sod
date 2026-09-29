import React from 'react';
import { createRoot } from 'react-dom/client';
import '../global.css';
import App from './App';

const runtimeRequire = (assetPath: string) => {
	const normalized = assetPath
		.replace(/^(\.\.\/)+/, '')
		.replace(/^\.\//, '');

	return `/${normalized}`;
};

(window as any).require = runtimeRequire;
(globalThis as any).require = runtimeRequire;

const container = document.getElementById('root')!;
const root = createRoot(container);
root.render(<App />);
