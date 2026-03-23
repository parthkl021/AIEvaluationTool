export interface DocEntry {
  title: string;
  navTitle?: string;
  url: string;
  githubUrl: string;
}

const GITHUB_OWNER = 'mathml42';
const GITHUB_REPO = 'AIEvaluationTool';
const GITHUB_BRANCH = 'himanshu_dev';
const GITHUB_DOCS_PATH = 'docs';

function buildRawDocUrl(fileName: string) {
  return `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${GITHUB_BRANCH}/${GITHUB_DOCS_PATH}/${fileName}`;
}

function buildGithubDocUrl(fileName: string) {
  return `https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/${GITHUB_DOCS_PATH}/${fileName}`;
}

const docsConfig = {
  overview: {
    title: 'Overview & Purpose',
    url: buildRawDocUrl('01-overview-and-purpose.md'),
    githubUrl: buildGithubDocUrl('01-overview-and-purpose.md'),
  },
  'architecture-design': {
    title: 'Architecture & Design',
    url: buildRawDocUrl('02-architecture-and-design.md'),
    githubUrl: buildGithubDocUrl('02-architecture-and-design.md'),
  },
  'docker-setup': {
    title: 'Docker Setup',
    url: buildRawDocUrl('03-getting-started-docker.md'),
    githubUrl: buildGithubDocUrl('03-getting-started-docker.md'),
  },
  'manual-setup': {
    title: 'Manual Setup',
    url: buildRawDocUrl('04-getting-started-manual.md'),
    githubUrl: buildGithubDocUrl('04-getting-started-manual.md'),
  },
  configuration: {
    title: 'Configuration',
    url: buildRawDocUrl('05-configuration.md'),
    githubUrl: buildGithubDocUrl('05-configuration.md'),
  },
  'ai-evaluation-tool': {
    title: 'AI Evaluation Tool',
    url: buildRawDocUrl('06-ai-evaluation-tool.md'),
    githubUrl: buildGithubDocUrl('06-ai-evaluation-tool.md'),
  },
  tdms: {
    title: 'TDMS',
    url: buildRawDocUrl('07-tdms.md'),
    githubUrl: buildGithubDocUrl('07-tdms.md'),
  },
  pqet: {
    title: 'PQET',
    url: buildRawDocUrl('08-pqet.md'),
    githubUrl: buildGithubDocUrl('08-pqet.md'),
  },
  'execution-dashboard': {
    title: 'Execution Dashboard',
    url: buildRawDocUrl('09-testcase-execution-dashboard.md'),
    githubUrl: buildGithubDocUrl('09-testcase-execution-dashboard.md'),
  },
  'project-history': {
    title: 'Project History',
    url: buildRawDocUrl('10-project-history.md'),
    githubUrl: buildGithubDocUrl('10-project-history.md'),
  },
};

export type DocId = keyof typeof docsConfig;

export const DOCS_CONFIG: Record<DocId, DocEntry> = docsConfig;

export const DOC_IDS = Object.keys(docsConfig) as DocId[];
