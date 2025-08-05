import { render, screen } from "@testing-library/react";
import Home from "../../../main/frontend/src/app/page";

describe("Home page", () => {
  it("renders title", () => {
    render(<Home />);
    expect(screen.getByText(/Traffic Intelligence Hub/i)).toBeInTheDocument();
  });
});
