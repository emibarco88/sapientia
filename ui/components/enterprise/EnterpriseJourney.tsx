import {
  BrainCircuit,
  Check,
  Database,
  Lightbulb,
  Search,
} from "lucide-react";

type JourneyStep = {
  title: string;
  description: string;
  complete: boolean;
  active?: boolean;
};

type EnterpriseJourneyProps = {
  connected: boolean;
  discovered: boolean;
  understood: boolean;
  intelligenceReady: boolean;
};

const STEP_ICONS = [Database, Search, BrainCircuit, Lightbulb];

export default function EnterpriseJourney({
  connected,
  discovered,
  understood,
  intelligenceReady,
}: EnterpriseJourneyProps) {
  const steps: JourneyStep[] = [
    {
      title: "Connect business information",
      description: "Bring together the data and documents that describe your business.",
      complete: connected,
      active: !connected,
    },
    {
      title: "Discover your enterprise",
      description: "Identify the business information available across your connected sources.",
      complete: discovered,
      active: connected && !discovered,
    },
    {
      title: "Learn how your business works",
      description: "Build an understanding of terminology, relationships and business meaning.",
      complete: understood,
      active: discovered && !understood,
    },
    {
      title: "Generate enterprise intelligence",
      description: "Create evidence-backed findings and make your intelligence ready to explore.",
      complete: intelligenceReady,
      active: understood && !intelligenceReady,
    },
  ];

  return (
    <div className="enterprise-journey">
      {steps.map((step, index) => {
        const Icon = STEP_ICONS[index];

        return (
          <div className="journey-step" key={step.title}>
            <div
              className={`journey-step-icon ${
                step.complete
                  ? "journey-step-icon-complete"
                  : step.active
                    ? "journey-step-icon-active"
                    : "journey-step-icon-pending"
              }`}
            >
              {step.complete ? (
                <Check aria-hidden="true" size={18} strokeWidth={2.5} />
              ) : (
                <Icon aria-hidden="true" size={18} strokeWidth={2} />
              )}
            </div>

            <div className="journey-step-content">
              <div className="journey-step-heading">
                <h3>{step.title}</h3>
                <span
                  className={`journey-status ${
                    step.complete
                      ? "journey-status-complete"
                      : step.active
                        ? "journey-status-active"
                        : "journey-status-pending"
                  }`}
                >
                  {step.complete ? "Complete" : step.active ? "Next" : "Waiting"}
                </span>
              </div>
              <p>{step.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
