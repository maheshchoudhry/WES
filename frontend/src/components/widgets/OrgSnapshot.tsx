import type { EmployeeDirectoryItem } from "../../api/dashboard";

interface Node {
  employee: EmployeeDirectoryItem;
  reports: Node[];
}

function buildTree(employees: EmployeeDirectoryItem[]): Node[] {
  const nodes = new Map<string, Node>();
  employees.forEach((e) => nodes.set(e.id, { employee: e, reports: [] }));
  const roots: Node[] = [];
  employees.forEach((e) => {
    const node = nodes.get(e.id)!;
    const parent = e.reports_to_id ? nodes.get(e.reports_to_id) : undefined;
    if (parent) parent.reports.push(node);
    else roots.push(node);
  });
  return roots;
}

function TreeNode({ node }: { node: Node }) {
  return (
    <li>
      <div className="org-node">
        <span className="org-name">{node.employee.full_name}</span>
        <span className="muted org-role">{node.employee.position}</span>
      </div>
      {node.reports.length > 0 && (
        <ul>
          {node.reports.map((child) => (
            <TreeNode key={child.employee.id} node={child} />
          ))}
        </ul>
      )}
    </li>
  );
}

/** Reusable organization / reporting-hierarchy snapshot widget. */
export function OrgSnapshot({ employees }: { employees: EmployeeDirectoryItem[] }) {
  if (employees.length === 0) {
    return <p className="muted">No employees to display.</p>;
  }
  const roots = buildTree(employees);
  return (
    <ul className="org-tree">
      {roots.map((root) => (
        <TreeNode key={root.employee.id} node={root} />
      ))}
    </ul>
  );
}
