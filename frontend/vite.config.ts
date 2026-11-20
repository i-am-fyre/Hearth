import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			// Static SPA: the backend serves these files and falls back to index.html.
			adapter: adapter({
				fallback: 'index.html'
			})
		})
	],
	ssr: {
		noExternal: ['chart.js']
	},
	server: {
		host: '0.0.0.0'
	}
});
