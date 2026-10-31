import { useParams } from "react-router-dom";
import PageHeader from "../components/common/PageHeader";
import LivePanel from "../components/experiments/LivePanel";

export default function LiveExperiment() {
  const { id } = useParams();
  return (
    <>
      <PageHeader title="Live experiment monitor" subtitle={id} />
      {id && <LivePanel experimentId={id} />}
    </>
  );
}
