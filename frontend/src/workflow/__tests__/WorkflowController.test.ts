import { describe, it, expect, jest } from "@jest/globals";
import { WorkflowController, NodeId, NodeStatus } from "../WorkflowController";

describe("WorkflowController", () => {
  // ── Initial State ──

  it("starts with node 1 ACTIVE and all others LOCKED", () => {
    const wc = new WorkflowController();
    const state = wc.getState();
    expect(state.nodes[NodeId.SELECTION].status).toBe(NodeStatus.ACTIVE);
    expect(state.nodes[NodeId.DEEP_READ].status).toBe(NodeStatus.LOCKED);
    expect(state.nodes[NodeId.DECONSTRUCT].status).toBe(NodeStatus.LOCKED);
    expect(state.nodes[NodeId.FILTER].status).toBe(NodeStatus.LOCKED);
    expect(state.nodes[NodeId.SKELETON].status).toBe(NodeStatus.LOCKED);
    expect(state.nodes[NodeId.IMITATE].status).toBe(NodeStatus.LOCKED);
    expect(state.nodes[NodeId.VALIDATE].status).toBe(NodeStatus.LOCKED);
  });

  it("initializes with no cooldown and default stage", () => {
    const wc = new WorkflowController();
    const state = wc.getState();
    expect(state.cooldownUntil).toBeNull();
    expect(state.canSubmitNewImitation).toBe(true);
    expect(state.dailySubmitCount).toBe(0);
    expect(state.stage).toBe("novice");
  });

  it("merges partial initial state with defaults", () => {
    const wc = new WorkflowController({ stage: "growing" });
    expect(wc.getState().stage).toBe("growing");
    expect(wc.getState().dailySubmitCount).toBe(0);
  });

  // ── canEnter ──

  it("allows entering SELECTION (node 1) from start", () => {
    const wc = new WorkflowController();
    expect(wc.canEnter(NodeId.SELECTION)).toBe(true);
  });

  it("blocks entering DEEP_READ (node 2) before SELECTION is complete", () => {
    const wc = new WorkflowController();
    expect(wc.canEnter(NodeId.DEEP_READ)).toBe(false);
  });

  it("allows entering deep read after completing selection", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    expect(wc.canEnter(NodeId.DEEP_READ)).toBe(true);
  });

  it("returns false for unknown node id", () => {
    const wc = new WorkflowController();
    expect(wc.canEnter(99 as NodeId)).toBe(false);
  });

  it("blocks completed nodes from being entered again", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    expect(wc.canEnter(NodeId.SELECTION)).toBe(false);
  });

  // ── completeNode → unlock chain ──

  it("unlocks node 2 after completing node 1", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    expect(wc.getState().nodes[NodeId.SELECTION].status).toBe(NodeStatus.COMPLETED);
    expect(wc.getState().nodes[NodeId.DEEP_READ].status).toBe(NodeStatus.ACTIVE);
  });

  it("completing a node beyond the first unlocks the next one", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    wc.completeNode(NodeId.DEEP_READ);
    wc.completeNode(NodeId.DECONSTRUCT);
    expect(wc.getState().nodes[NodeId.FILTER].status).toBe(NodeStatus.ACTIVE);
  });

  it("completing last node (VALIDATE) does not crash", () => {
    const wc = new WorkflowController();
    for (let i = NodeId.SELECTION; i <= NodeId.VALIDATE; i++) {
      wc.completeNode(i as NodeId);
    }
    expect(wc.getState().nodes[NodeId.VALIDATE].status).toBe(NodeStatus.COMPLETED);
  });

  it("double-completing the same node is idempotent", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    wc.completeNode(NodeId.SELECTION); // second call
    expect(wc.getState().nodes[NodeId.SELECTION].status).toBe(NodeStatus.COMPLETED);
    expect(wc.getState().nodes[NodeId.DEEP_READ].status).toBe(NodeStatus.ACTIVE);
  });

  // ── Cooldown ──

  it("setCooldown locks human nodes to COOLDOWN status", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    wc.completeNode(NodeId.DEEP_READ);
    wc.completeNode(NodeId.DECONSTRUCT); // FILTER (node 4) is now ACTIVE
    wc.setCooldown(2);
    expect(wc.getState().nodes[NodeId.FILTER].status).toBe(NodeStatus.COOLDOWN);
    expect(wc.getState().cooldownUntil).not.toBeNull();
    expect(wc.getState().canSubmitNewImitation).toBe(false);
  });

  it("clearCooldown restores COOLDOWN nodes to ACTIVE", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    wc.completeNode(NodeId.DEEP_READ);
    wc.completeNode(NodeId.DECONSTRUCT);
    wc.setCooldown(1);
    wc.clearCooldown();
    expect(wc.getState().nodes[NodeId.FILTER].status).toBe(NodeStatus.ACTIVE);
    expect(wc.getState().cooldownUntil).toBeNull();
    expect(wc.getState().canSubmitNewImitation).toBe(true);
  });

  it("isLockedByCooldown returns true during cooldown", () => {
    const wc = new WorkflowController();
    wc.setCooldown(1);
    expect(wc.isLockedByCooldown()).toBe(true);
  });

  it("isLockedByCooldown returns false after clearCooldown", () => {
    const wc = new WorkflowController();
    wc.setCooldown(1);
    wc.clearCooldown();
    expect(wc.isLockedByCooldown()).toBe(false);
  });

  it("isLockedByCooldown returns false when no cooldown was set", () => {
    const wc = new WorkflowController();
    expect(wc.isLockedByCooldown()).toBe(false);
  });

  it("canEnter respects cooldown for human-entry nodes", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    wc.completeNode(NodeId.DEEP_READ);
    wc.completeNode(NodeId.DECONSTRUCT);
    wc.setCooldown(1);
    // Human-node FILTER is COOLDOWN, so canEnter should be false
    expect(wc.canEnter(NodeId.FILTER)).toBe(false);
  });

  // ── dailySubmitCount ──

  it("incrementDailyCount toggles canSubmitNewImitation after first call", () => {
    const wc = new WorkflowController();
    expect(wc.getState().canSubmitNewImitation).toBe(true);
    wc.incrementDailyCount();
    expect(wc.getState().dailySubmitCount).toBe(1);
    expect(wc.getState().canSubmitNewImitation).toBe(false);
  });

  // ── reset ──

  it("reset restores initial state while preserving listeners", () => {
    const wc = new WorkflowController();
    wc.completeNode(NodeId.SELECTION);
    wc.completeNode(NodeId.DEEP_READ);
    wc.setCooldown(2);
    wc.incrementDailyCount();
    wc.reset();
    expect(wc.getState().nodes[NodeId.SELECTION].status).toBe(NodeStatus.ACTIVE);
    expect(wc.getState().nodes[NodeId.DEEP_READ].status).toBe(NodeStatus.LOCKED);
    expect(wc.getState().cooldownUntil).toBeNull();
    expect(wc.getState().canSubmitNewImitation).toBe(true);
  });

  // ── subscribe ──

  it("subscribe calls listener on state changes", () => {
    const wc = new WorkflowController();
    const listener = jest.fn();
    wc.subscribe(listener);
    wc.completeNode(NodeId.SELECTION);
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it("subscribe returns unsubscribe function", () => {
    const wc = new WorkflowController();
    const listener = jest.fn();
    const unsubscribe = wc.subscribe(listener);
    unsubscribe();
    wc.completeNode(NodeId.SELECTION);
    expect(listener).not.toHaveBeenCalled();
  });

  it("multiple listeners all receive notifications", () => {
    const wc = new WorkflowController();
    const a = jest.fn();
    const b = jest.fn();
    wc.subscribe(a);
    wc.subscribe(b);
    wc.completeNode(NodeId.SELECTION);
    expect(a).toHaveBeenCalledTimes(1);
    expect(b).toHaveBeenCalledTimes(1);
  });
});
