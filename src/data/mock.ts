export type RiskBand = 'Low' | 'Medium' | 'High'

export type Listing = {
  id: number
  title: string
  company: string
  trustScore: number
  risk: RiskBand
  stipend: string
  mode: 'Remote' | 'Hybrid' | 'On-site'
  duration: string
  tags: string[]
  verdict: string
  role: string
  growth: string
  location: string
  greenFlags: string[]
  redFlags: string[]
  verificationSources: string[]
  detectedPatterns: string[]
}

export type CategoryPreset = {
  name: string
  subtitle: string
  description: string
}

export const categoryPresets: CategoryPreset[] = [
  {
    name: 'Internships',
    subtitle: 'Default demo',
    description: 'Detect fake internship posts, verify recruiters, and compare genuine opportunities.',
  },
  {
    name: 'PGs',
    subtitle: 'Housing safety',
    description: 'Detect fake listings, compare rent signals, and verify owner credibility.',
  },
  {
    name: 'Scholarships',
    subtitle: 'Deadline ready',
    description: 'Find genuine scholarships, flag paid forms, and track eligibility or deadlines.',
  },
  {
    name: 'Hackathons',
    subtitle: 'Event credibility',
    description: 'Verify organizers, prize claims, and team-fit signals before you register.',
  },
  {
    name: 'Used Laptops',
    subtitle: 'Seller trust',
    description: 'Check warranty claims, price history, and suspicious seller behavior.',
  },
  {
    name: 'Courses',
    subtitle: 'Learning value',
    description: 'Analyze refunds, placement claims, and real learner feedback quality.',
  },
  {
    name: 'Food Places',
    subtitle: 'Local trust',
    description: 'Spot fake reviews, menu mismatches, and risky order patterns.',
  },
  {
    name: 'Local Services',
    subtitle: 'Service safety',
    description: 'Verify credentials, compare market pricing, and detect scammy contact flows.',
  },
]

export const roleFilters = ['Frontend', 'AI/ML', 'Backend', 'Design', 'Marketing']
export const modeFilters = ['Remote', 'Hybrid', 'On-site']
export const stipendFilters = ['Any', 'Paid only', '₹5k+', '₹10k+']
export const riskFilters = ['Low risk only']
export const growthFilters = ['High growth roles']

export const categoryChips = [
  'Internships',
  'PGs',
  'Scholarships',
  'Hackathons',
  'Used Laptops',
  'Courses',
  'Food Places',
  'Local Services',
]

export const listings: Listing[] = [
  {
    id: 1,
    title: 'Frontend Developer Intern',
    company: 'Nova Labs',
    trustScore: 88,
    risk: 'Low',
    stipend: '₹12k/month',
    mode: 'Remote',
    duration: '2 months',
    tags: ['React', 'TypeScript', 'UI'],
    verdict:
      'Strong match. Real company presence, clear stipend, and no upfront payment request.',
    role: 'Frontend',
    growth: 'High',
    location: 'Remote-first',
    greenFlags: [
      'Company website and LinkedIn are consistent',
      'Clear stipend and duration mentioned',
      'No application fee requested',
      'Recruiter profile has history',
      'Role requirements match internship level',
    ],
    redFlags: ['Company is relatively new', 'Few public employee reviews', 'Limited GitHub/technical presence'],
    verificationSources: [
      'Website check',
      'LinkedIn check',
      'Review pattern check',
      'Domain age signal',
      'Similar post comparison',
      'Fee request detection',
    ],
    detectedPatterns: [
      'No upfront payment',
      'No unrealistic salary claim',
      'No copied job description',
      'No suspicious WhatsApp-only contact',
      'No certificate-selling language',
    ],
  },
  {
    id: 2,
    title: 'AI Research Intern',
    company: 'NeuralBridge',
    trustScore: 81,
    risk: 'Medium',
    stipend: '₹8k/month',
    mode: 'Hybrid',
    duration: '3 months',
    tags: ['Python', 'ML', 'Research'],
    verdict: 'Looks promising, but the company profile is new. Apply only through verified channels.',
    role: 'AI/ML',
    growth: 'High',
    location: 'Hybrid',
    greenFlags: ['Clear project scope', 'Relevant ML stack', 'Public founder footprint'],
    redFlags: ['Company profile is new', 'Limited alumni feedback', 'Low external mentions'],
    verificationSources: ['Website check', 'Founder profile check', 'Review pattern check', 'Domain age signal'],
    detectedPatterns: ['No payment demand', 'No repeated copy-paste scam pattern', 'Limited public history'],
  },
  {
    id: 3,
    title: 'Data Analyst Intern',
    company: 'SkillGrow Careers',
    trustScore: 42,
    risk: 'High',
    stipend: 'Certificate only',
    mode: 'Remote',
    duration: '1 month',
    tags: ['Excel', 'SQL', 'Dashboard'],
    verdict: 'Risky. Vague company details, repeated review patterns, and unclear deliverables.',
    role: 'Backend',
    growth: 'Low',
    location: 'Remote',
    greenFlags: ['Basic role title present'],
    redFlags: [
      'No clear stipend or compensation flow',
      'Vague company identity',
      'Repeated testimonial language',
      'Unclear deliverables',
      'Requests a quick WhatsApp response',
    ],
    verificationSources: ['Website check', 'Review pattern check', 'Fee request detection'],
    detectedPatterns: ['Certificate-selling language', 'Suspicious contact channel', 'Inconsistent company footprint'],
  },
  {
    id: 4,
    title: 'Backend Intern',
    company: 'CloudNest',
    trustScore: 91,
    risk: 'Low',
    stipend: '₹15k/month',
    mode: 'Remote',
    duration: '3 months',
    tags: ['Node.js', 'APIs', 'PostgreSQL'],
    verdict: 'Highly trusted. Good company footprint, clear role description, and verified recruiter.',
    role: 'Backend',
    growth: 'High',
    location: 'Remote-first',
    greenFlags: [
      'Verified recruiter profile',
      'Consistent role details across sources',
      'High-quality company footprint',
      'Clear stipend and responsibilities',
      'No payment request',
    ],
    redFlags: ['Small public team size', 'Short company history'],
    verificationSources: ['Website check', 'LinkedIn check', 'Domain age signal', 'Similar post comparison'],
    detectedPatterns: ['No upfront payment', 'No false promise pattern', 'No scammy urgency language'],
  },
  {
    id: 5,
    title: 'Product Design Intern',
    company: 'Auric Studio',
    trustScore: 77,
    risk: 'Low',
    stipend: '₹10k/month',
    mode: 'Hybrid',
    duration: '2 months',
    tags: ['Figma', 'Research', 'Prototyping'],
    verdict: 'Solid option. Portfolio-friendly work and a believable team profile.',
    role: 'Design',
    growth: 'Medium',
    location: 'Bengaluru hybrid',
    greenFlags: ['Portfolio work visible', 'Clear mentor contact', 'Good project scope'],
    redFlags: ['Smaller external footprint'],
    verificationSources: ['Website check', 'Mentor profile check', 'Review pattern check'],
    detectedPatterns: ['No fee request', 'No salary exaggeration', 'No hidden assignment trap'],
  },
  {
    id: 6,
    title: 'Growth Marketing Intern',
    company: 'LoopSpark',
    trustScore: 66,
    risk: 'Medium',
    stipend: '₹6k/month',
    mode: 'On-site',
    duration: '2 months',
    tags: ['Content', 'SEO', 'Campaigns'],
    verdict: 'Possible, but the role is broader and the company profile needs more verification.',
    role: 'Marketing',
    growth: 'High',
    location: 'Delhi on-site',
    greenFlags: ['Specific campaign work mentioned', 'Reasonable stipend'],
    redFlags: ['Limited proof of business traction', 'Short recruiter history', 'Few independent mentions'],
    verificationSources: ['Website check', 'LinkedIn check', 'Review pattern check', 'Domain age signal'],
    detectedPatterns: ['No upfront fee', 'No WhatsApp-only gate', 'No copied template red flags'],
  },
]

export const growthTrend = {
  labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
  series: {
    Frontend: [18, 22, 28, 35],
    'AI/ML': [12, 18, 25, 31],
    Backend: [15, 17, 19, 22],
  },
}

export const riskDistribution = [
  { label: 'Low Risk', value: 48 },
  { label: 'Medium Risk', value: 31 },
  { label: 'High Risk', value: 21 },
]

export const recommendationSummary = [
  {
    label: 'Safest Option',
    title: 'Backend Intern — CloudNest',
    detail: 'Highest trust score among paid internships.',
  },
  {
    label: 'Fastest Growing',
    title: 'AI Research Intern — NeuralBridge',
    detail: 'Strong signal in AI/ML demand this month.',
  },
  {
    label: 'Best Remote Option',
    title: 'Frontend Developer Intern — Nova Labs',
    detail: 'Great fit if you want a remote UI-focused role.',
  },
  {
    label: 'Avoid',
    title: 'Data Analyst Intern — SkillGrow Careers',
    detail: 'Risk is too high without better verification.',
  },
]

export const useCaseCards = [
  {
    title: 'PG Finder',
    description: 'Detect fake listings, verify owners, compare rent, and map student housing density.',
  },
  {
    title: 'Scholarship Verifier',
    description: 'Find genuine scholarships, check eligibility, detect fake paid forms, and track deadlines.',
  },
  {
    title: 'Used Laptop Checker',
    description: 'Detect suspicious sellers, compare price history, check warranty claims, and suggest fair negotiation.',
  },
  {
    title: 'Hackathon Finder',
    description: 'Verify events, detect fake prize claims, check organizer credibility, and recommend the best fit.',
  },
  {
    title: 'Course Authenticity Checker',
    description: 'Analyze placement claims, refund policies, testimonials, and the real learning value.',
  },
]
