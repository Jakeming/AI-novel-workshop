/**
 * WorkflowController.ts — Frontend state machine (Candidate 5).
 *
 * Deep module: one source of truth for 7-node workflow state.
 * UI components only read — never mutate directly.
 */

export enum NodeId {
  SELECTION = 1,    // 节点1 选文导入
  DEEP_READ = 2,    // 节点2 AI深度精读
  DECONSTRUCT = 3,  // 节点3 分层拆解
  FILTER = 4,       // 节点4 灵气筛选 🧑
  SKELETON = 5,     // 节点5 生成骨架
  IMITATE = 6,      // 节点6 仿写重构 🧑
  VALIDATE = 7,     // 节点7 校验复盘
}

export enum NodeStatus {
  LOCKED = "locked",
  ACTIVE = "active",
  COMPLETED = "completed",
  COOLDOWN = "cooldown",
}

export interface NodeState {
  id: NodeId;
  status: NodeStatus;
  label: string;
  requiresHuman: boolean;  // true for 节点4, 节点6
}

export interface WorkflowState {
  nodes: Record<NodeId, NodeState>;
  cooldownUntil: Date | null;
  canSubmitNewImitation: boolean;
  dailySubmitCount: number;
  stage: "novice" | "growing" | "mature";
}

type Listener = (state: WorkflowState) => void;

export class WorkflowController {
  private state: WorkflowState;
  private listeners: Set<Listener> = new Set();

  constructor(initial?: Partial<WorkflowState>) {
    this.state = {
      nodes: {
        [NodeId.SELECTION]:    { id: NodeId.SELECTION,    status: NodeStatus.ACTIVE,    label: "选文导入",       requiresHuman: false },
        [NodeId.DEEP_READ]:    { id: NodeId.DEEP_READ,    status: NodeStatus.LOCKED,    label: "AI深度精读",      requiresHuman: false },
        [NodeId.DECONSTRUCT]:  { id: NodeId.DECONSTRUCT,  status: NodeStatus.LOCKED,    label: "分层拆解",        requiresHuman: false },
        [NodeId.FILTER]:       { id: NodeId.FILTER,       status: NodeStatus.LOCKED,    label: "灵气筛选",        requiresHuman: true },
        [NodeId.SKELETON]:     { id: NodeId.SKELETON,     status: NodeStatus.LOCKED,    label: "生成骨架",        requiresHuman: false },
        [NodeId.IMITATE]:      { id: NodeId.IMITATE,      status: NodeStatus.LOCKED,    label: "仿写重构",        requiresHuman: true },
        [NodeId.VALIDATE]:     { id: NodeId.VALIDATE,     status: NodeStatus.LOCKED,    label: "校验复盘",        requiresHuman: false },
      },
      cooldownUntil: null,
      canSubmitNewImitation: true,
      dailySubmitCount: 0,
      stage: "novice",
      ...initial,
    };
  }

  // --- Read-only queries for UI components ---

  getState(): WorkflowState {
    return this.state;
  }

  canEnter(nodeId: NodeId): boolean {
    const node = this.state.nodes[nodeId];
    if (!node) return false;
    if (node.status === NodeStatus.COMPLETED) return false;
    if (this.state.cooldownUntil && new Date() < this.state.cooldownUntil) {
      return node.requiresHuman ? node.status === NodeStatus.ACTIVE : false;
    }
    // Dependency: node N requires node N-1 complete
    if (nodeId > NodeId.SELECTION) {
      const prev = this.state.nodes[nodeId - 1 as NodeId];
      if (prev && prev.status !== NodeStatus.COMPLETED) return false;
    }
    return node.status === NodeStatus.ACTIVE || node.status === NodeStatus.LOCKED;
  }

  isLockedByCooldown(): boolean {
    return !!this.state.cooldownUntil && new Date() < this.state.cooldownUntil;
  }

  // --- Mutations (called by workflow logic, not UI) ---

  completeNode(nodeId: NodeId): void {
    const node = this.state.nodes[nodeId];
    if (!node || node.status === NodeStatus.COMPLETED) return;
    node.status = NodeStatus.COMPLETED;

    // Unlock next node
    const nextId = (nodeId + 1) as NodeId;
    const next = this.state.nodes[nextId];
    if (next && next.status === NodeStatus.LOCKED) {
      next.status = NodeStatus.ACTIVE;
    }

    this._notify();
  }

  setCooldown(hours: number): void {
    const until = new Date(Date.now() + hours * 3600_000);
    this.state.cooldownUntil = until;
    this.state.canSubmitNewImitation = false;

    // Lock all human-entry nodes except active one
    for (const n of Object.values(this.state.nodes)) {
      if (n.requiresHuman && n.status === NodeStatus.ACTIVE) {
        n.status = NodeStatus.COOLDOWN;
      }
    }
    this._notify();
  }

  clearCooldown(): void {
    this.state.cooldownUntil = null;
    this.state.canSubmitNewImitation = true;
    for (const n of Object.values(this.state.nodes)) {
      if (n.status === NodeStatus.COOLDOWN) {
        n.status = NodeStatus.ACTIVE;
      }
    }
    this._notify();
  }

  incrementDailyCount(): void {
    this.state.dailySubmitCount++;
    if (this.state.dailySubmitCount >= 1) {
      this.state.canSubmitNewImitation = false;
    }
    this._notify();
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private _notify(): void {
    for (const fn of this.listeners) {
      fn(this.state);
    }
  }

  /** Reset for new deconstruction session */
  reset(): void {
    for (const node of Object.values(this.state.nodes)) {
      node.status = NodeStatus.LOCKED;
    }
    this.state.nodes[NodeId.SELECTION].status = NodeStatus.ACTIVE;
    this.state.cooldownUntil = null;
    this.state.canSubmitNewImitation = true;
    this._notify();
  }
}
