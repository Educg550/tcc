import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          Test-Oriented Programming + CUA
        </Heading>
        <p className="hero__subtitle">
          O que a validação comportamental via CUA detecta que pipelines TDD+LLM deixam passar?
        </p>
        <p className={styles.meta}>
          Eduardo Cruz Guedes · NUSP 13672752 · BCC IME-USP · 5º ano
          <br />
          Orientadores: Prof. Paulo Meirelles · Prof. Jorge Melegati
        </p>
        <div className={styles.buttons}>
          <Link className="button button--secondary button--lg" to="/docs/intro">
            Ver Documentação
          </Link>
          <Link className="button button--outline button--secondary button--lg" to="/docs/proposta">
            Proposta de Pesquisa
          </Link>
        </div>
      </div>
    </header>
  );
}

type CardItem = {
  title: string;
  description: ReactNode;
  link: string;
  linkLabel: string;
};

const cards: CardItem[] = [
  {
    title: 'Proposta de Pesquisa',
    description: 'Baseline: pipeline TDD+LLM (paradigma TOP / Onion). Experimental: mesmo pipeline com CUA como avaliador comportamental final.',
    link: '/docs/proposta',
    linkLabel: 'Ler proposta',
  },
  {
    title: 'Metodologia',
    description: 'Métricas estruturais (CI, ciclomática, mutação) e comportamentais (CUA). Escopo: sistema com frontend, 10–20 requisitos fechados.',
    link: '/docs/metodologia',
    linkLabel: 'Ver metodologia',
  },
  {
    title: 'Referências',
    description: 'Paper TOP (ICSE 2026), ferramenta Onion, benchmarks de CUAs, TDD com Uncle Bob e pipelines open source de orquestração.',
    link: '/docs/referencias',
    linkLabel: 'Ver referências',
  },
];

function Card({title, description, link, linkLabel}: CardItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className={clsx('card', styles.card)}>
        <div className="card__header">
          <Heading as="h3">{title}</Heading>
        </div>
        <div className="card__body">
          <p>{description}</p>
        </div>
        <div className="card__footer">
          <Link className="button button--primary button--block" to={link}>
            {linkLabel}
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
        <section className={styles.cards}>
          <div className="container">
            <div className="row">
              {cards.map((card, idx) => (
                <Card key={idx} {...card} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
