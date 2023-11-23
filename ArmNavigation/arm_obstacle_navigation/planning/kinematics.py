import numpy as np
import torch
from scipy.interpolate import interp1d


def forward_kinematics(
    link_lengths,
    joint_angles,
) -> torch.Tensor:
    """
    Returns:
        joints_pose: N x 2 matrix of joint X,Y coorindates
    """
    joints_pose = torch.zeros((len(joint_angles) + 1, 2))
    theta_sum = torch.tensor(0.0)
    for i, theta in enumerate(joint_angles):
        theta_sum += theta
        xy = torch.tensor(
            [
                torch.cos(theta_sum) * link_lengths[i],
                torch.sin(theta_sum) * link_lengths[i],
            ]
        )
        joints_pose[i + 1, :] = joints_pose[i, :] + xy

    return joints_pose


def jacobian(
    link_lengths: torch.Tensor,
    joint_angles: torch.Tensor,
) -> torch.Tensor:
    joints_pose = forward_kinematics(link_lengths, joint_angles)
    ee_pose = joints_pose[-1, :]
    jac = torch.zeros((2, len(joint_angles)))
    for i, joint_pose in enumerate(joints_pose[:-1]):
        ee_from_joint_pose = ee_pose - joint_pose
        ee_from_joint_ang = torch.atan2(ee_from_joint_pose[1], ee_from_joint_pose[0])
        ee_from_joint_norm = torch.norm(ee_from_joint_pose)

        dx = -torch.sin(ee_from_joint_ang) * ee_from_joint_norm
        dy = torch.cos(ee_from_joint_ang) * ee_from_joint_norm
        jac[0, i] = dx
        jac[1, i] = dy

    return jac


def inverse_kinematics(
    link_lengths: torch.Tensor,
    joint_angles: torch.Tensor,
    target: torch.Tensor,
    max_iteration: int = 1000,
) -> tuple[torch.Tensor, bool]:
    iter = 0
    cur_joint_angles = joint_angles.clone()
    damping = torch.tensor(0.1)
    while iter < max_iteration:
        cur_pose = forward_kinematics(link_lengths, cur_joint_angles)[-1, :]
        delta_pose = target - cur_pose
        dist = torch.norm(delta_pose)
        if dist.item() < 0.01:
            return cur_joint_angles, True

        # Calculate the difference using the pseudo-inverse of the Jacobian
        delta_angles = (
            torch.pinverse(jacobian(link_lengths, cur_joint_angles))
            @ (target - cur_pose)
            * damping
        )
        cur_joint_angles = cur_joint_angles + delta_angles
        iter += 1

    return cur_joint_angles, False


def resample_trajectory(trajectory: torch.Tensor, num_points: int) -> torch.Tensor:
    """
    Resamples a trajectory to have a specific number of points using linear interpolation.

    Args:
        trajectory: A D by N tensor where D is the dimensionality and N is the number of points.
        num_points: The number of points in the resampled trajectory.

    Returns:
        A D by num_points tensor representing the resampled trajectory.
    """
    if trajectory.size(1) <= 1:
        raise ValueError("Trajectory must have more than one point.")

    trajectory_np = trajectory.numpy()
    current_indices = np.linspace(0, 1, trajectory_np.shape[1])
    new_indices = np.linspace(0, 1, num_points)
    interpolator = interp1d(current_indices, trajectory_np, axis=1, kind="linear")
    new_trajectory_np = interpolator(new_indices)

    new_trajectory = torch.from_numpy(new_trajectory_np)
    return new_trajectory