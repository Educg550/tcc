import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'TCC — Eduardo Cruz Guedes',
  tagline: 'Pipeline Multiagente com TDD e Validação via CUA',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  url: 'https://educg550.github.io',
  baseUrl: '/tcc/',

  organizationName: 'Educg550',
  projectName: 'tcc',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'pt-BR',
    locales: ['pt-BR'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/Educg550/tcc/tree/main/',
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          editUrl: 'https://github.com/Educg550/tcc/tree/main/',
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'TCC — Eduardo Cruz Guedes',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Documentação',
        },
        {to: '/blog', label: 'Diário de Pesquisa', position: 'left'},
        {
          href: 'https://github.com/Educg550/tcc',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'TCC',
          items: [
            {label: 'Visão Geral', to: '/docs/intro'},
            {label: 'Proposta de Pesquisa', to: '/docs/proposta'},
            {label: 'Metodologia', to: '/docs/metodologia'},
            {label: 'Referências', to: '/docs/referencias'},
          ],
        },
        {
          title: 'Links',
          items: [
            {label: 'GitHub', href: 'https://github.com/Educg550/tcc'},
            {label: 'Diário de Pesquisa', to: '/blog'},
          ],
        },
      ],
      copyright: `Eduardo Cruz Guedes (educg550@usp.br) — NUSP 13672752 — BCC IME-USP · Orientadores: Prof. Paulo Meirelles & Prof. Jorge Melegati`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
