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
          Avaliação de pipelines multiagente de geração de código: geração direta, TDD e reconstrução guiada por testes
        </Heading>
        <p className="hero__subtitle">
          A geração com TDD produz código com maior corretude funcional do que a geração direta?
        </p>
        <p className={styles.meta}>
          Eduardo Cruz Guedes · NUSP 13672752 · BCC IME-USP · 5º ano
          <br />
          Orientadores: Prof. Paulo Meirelles · Prof. Jorge Melegati
        </p>
        <Link className={clsx('button button--secondary button--lg', styles.monografia)} href="pathname:///monografia.pdf">
          Ler a monografia (PDF)
        </Link>
        <div className={styles.buttons}>
          <Link className="button button--outline button--secondary" to="/docs/intro">
            Ver Documentação
          </Link>
          <Link className="button button--outline button--secondary" to="/docs/proposta">
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
    description: 'Proposta inicial de avaliação com CUA e extensão para a reconstrução do PreJanus-back.',
    link: '/docs/proposta',
    linkLabel: 'Ler proposta',
  },
  {
    title: 'Metodologia',
    description: 'Experimento com o formulário de auxílio financeiro e reconstrução do PreJanus-back. Comparamos os pipelines pelo consumo de tokens e pelo desempenho em testes de aceitação independentes deles.',
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
