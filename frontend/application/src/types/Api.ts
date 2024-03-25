interface StudyListItem {
  handle: string;
  display_name_detail: string;
}

export type StudyList = StudyListItem[];

export interface SpatialMetricData {
  identifier: string;
  is_pending: boolean;
  values: { [key: string]: number | null };
}

export interface CCGNMetricData {
  identifier: string;
  is_pending: boolean;
  counts: { specimen: string; percentage: number }[];
}

export interface StudySummary {
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
