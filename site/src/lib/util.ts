// Prefija rutas internas con el base path (GitHub Pages de proyecto).
export function u(path: string): string {
  const base = import.meta.env.BASE_URL;
  return (base.endsWith('/') ? base : base + '/') + path.replace(/^\//, '');
}

// Paleta por artista, heredada del prototipo mapa-del-prog.html.
export const COLORES: Record<string, string> = {
  who: '#E4572E', npr: '#B08D57', mb: '#6672B8', pf: '#3E8E5A', kc: '#C0263B',
  gen: '#E56CA5', yes: '#4E7DD4', elp: '#8E6FC1', jt: '#6B8E3A', vdgg: '#7C8363',
  gg: '#D08C2E', car: '#C98CA7', sm: '#8A79B5', cam: '#C2A46B', mo: '#58A4B0',
  app: '#A93F55', ap: '#88A47C', rush: '#B04A5A', sup: '#D9B44A', elo: '#6E9FD4',
  foc: '#58B08A', ren: '#C77E5A', str: '#9C8AA5', ca: '#D9587E', bjh: '#8FA35C',
  sh: '#4FA3A5',
};

// Color por tipo de arista (apagados, para fondo oscuro). También son la leyenda.
export const COLORES_ARISTA: Record<string, string> = {
  member_of: '#6E7F95',
  produced: '#C08A45',
  engineered: '#7D9A6A',
  arranged: '#9A78C0',
  guested_on: '#5AA0C8',
  designed_artwork: '#C9739C',
  signed_to: '#D9B44A',
  recorded_at: '#7C8878',
  wrote_lyrics: '#C96F6F',
};

export const NOMBRES_ARISTA: Record<string, string> = {
  member_of: 'miembros',
  produced: 'producción',
  engineered: 'ingeniería',
  arranged: 'arreglos',
  guested_on: 'invitados',
  designed_artwork: 'arte de tapa',
  signed_to: 'sellos',
  recorded_at: 'estudios',
  wrote_lyrics: 'letras',
};

export const ESTADO_CHARTS: Record<string, string> = {
  verificado: 'verificado contra fuentes',
  parcial: 'verificación parcial',
  memoria: 'sin verificar — tratar como s.d.',
  sd: 's.d. — sin dato',
};

export const ERAS: Record<string, { nombre: string; rango: string; orden: number }> = {
  clasica: { nombre: 'Era clásica', rango: '1966–1980', orden: 1 },
  siguiente: { nombre: 'La continuación', rango: '1981–1999', orden: 2 },
  moderna: { nombre: 'Era moderna', rango: '2000–hoy', orden: 3 },
};

// ★★★☆☆ — null = sin valoración
export function estrellas(n: number | null | undefined): string {
  if (n == null) return 's.d.';
  const k = Math.max(1, Math.min(5, Math.round(n)));
  return '★'.repeat(k) + '☆'.repeat(5 - k);
}
