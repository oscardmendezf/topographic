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

export const ESTADO_CHARTS: Record<string, string> = {
  verificado: 'verificado contra fuentes',
  parcial: 'verificación parcial',
  memoria: 'sin verificar — tratar como s.d.',
};
