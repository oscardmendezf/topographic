import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

// La capa editorial vive en /content (raíz del repo), fuera de site/.
const artistas = defineCollection({
  loader: glob({ pattern: '*.md', base: '../content/artistas' }),
});
const albumes = defineCollection({
  loader: glob({ pattern: '*.md', base: '../content/albumes' }),
});
const red = defineCollection({
  loader: glob({ pattern: '*.md', base: '../content/red' }),
});
const etapas = defineCollection({
  loader: glob({ pattern: '*.md', base: '../content/etapas' }),
});

export const collections = { artistas, albumes, red, etapas };
