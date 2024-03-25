export interface StudyData {
  summary?: Summary;
  channels?: Channel[];
  baseCounts?: BaseCounts;
  symbols?: Symbol[];
  visualizationPlots?: VisualizationPlot[];
  selectedPhenotypes?: Symbol[];
  customPhenotypes?: Symbol[];
}

export interface PhenotypesData extends BaseCounts {
  average: number;
  handle_string: string;
}

export interface SelectedPhenotype extends Omit<Phenotype, "identifier"> {
  criteriaDetail?: {
    first: Criteria;
    second: Criteria;
  };
}

export interface SpatialData {
  isSpatial: boolean;
  metric: string;
  phenotype: string;
}

export interface VisualizationPlot {
  channel: string;
  base64_png: string;
}

interface Summary {
  context: Context;
  products: Products;
  counts: Counts;
  cohorts: Cohorts;
}

interface Context {
  institution: Institution;
  assay: Assay;
  contact: Contact;
}

interface Institution {
  name: string;
}

interface Assay {
  name: string;
}

interface Contact {
  name: string;
  email_address: string;
}

interface Products {
  data_release: DataRelease;
  publication: Publication;
}

interface DataRelease {
  repository: string;
  url: string;
  date: string;
}

interface Publication {
  title: string;
  url: string;
  first_author_name: string;
  date: string;
}

interface Counts {
  specimens: number;
  cells: number;
  channels: number;
  composite_phenotypes: number;
}

interface Cohorts {
  assignments: Assignment[];
  cohorts: Cohort[];
}

interface Assignment {
  sample: string;
  cohort: string;
}

interface Cohort {
  identifier: string;
  temporality: string;
  diagnosis: string;
  result: string;
}

export interface Channel {
  symbol: string;
}

export interface BaseCounts {
  counts: Count[];
  phenotype: Phenotype;
  number_cells_in_study: number;
}

interface Count {
  specimen: string;
  count: number;
  percentage: number;
}

interface Phenotype {
  name: string;
  identifier: string;
  criteria: Criteria;
}

export interface Criteria {
  positive_markers: string[];
  negative_markers: string[];
}

export interface Symbol {
  handle_string: string;
  identifier: string;
  criteria?: Criteria;
}
