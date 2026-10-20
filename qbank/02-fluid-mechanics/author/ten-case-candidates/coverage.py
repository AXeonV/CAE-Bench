"""Scientific coverage targets, deliberately distinct from achieved evidence.

Index lists refer to the ten scenario proposals in scenarios.py (one-based).
An assignment describes a design intention, never proof that a case implements it.
"""

FEATURES = {
    "closed_flow": [
        ("no_slip_and_moving_wall", [1,9,10]), ("velocity_inlet_and_full_pressure_traction", [2,5]),
        ("general_vector_traction", [3]), ("periodic_without_pressure_jump", [4]),
        ("symmetry", [5]), ("perfect_slip", [6]), ("nonzero_compatible_initial_velocity", [6]),
        ("uniform_time_varying_acceleration", [4]), ("spatially_varying_nonconservative_acceleration", [7]),
        ("flow_rate_with_nonuniform_shape", [8]), ("internal_obstacle_boundary", [8]),
        ("mean_pressure_gauge", [1,4,6,9,10]), ("point_pressure_gauge", [7]),
        ("pressure_fixed_by_traction_no_extra_gauge", [2,3,5,8]),
        ("ramp_pulse_reversal_histories", [1,9,10]),
        ("constant_linear_previous_input_reconstruction", [1,4,7]),
        ("nodal_piecewise_linear_and_entity_constant_inputs", [2,6,7,8]),
        ("velocity_pressure_density_viscosity_shear_rate", [1,2,6]),
        ("boundary_traction_force_and_signed_flows", [3,8]),
        ("point_cell_average_and_region_mean_observations", [2,6,7]),
    ],
    "generalized_flow": [
        ("clipped_power_law_shear_thinning", [1,6,10]), ("clipped_power_law_shear_thickening", [2]),
        ("low_and_high_shear_cutoffs", [6]), ("cross_both_plateaus_and_transition", [3,7]),
        ("carreau", [4,8]), ("carreau_yasuda_independent_exponent", [5,9]),
        ("velocity_reservoir_and_flow_rate", [1,3,5]), ("periodic_body_force", [2]),
        ("vector_traction", [6]), ("slip_and_symmetry", [5,9]),
        ("moving_walls", [4,8,10]), ("spatial_source_and_point_pressure", [7]),
        ("inner_boundary", [3]), ("viscosity_shear_rate_stress_force_and_flows", [1,3,6]),
        ("transient_nonzero_initial_and_history_or_steady_unique_state", [8,10]),
    ],
    "isothermal_compressible": [
        ("ideal_gas_eos", [1,3,5,6,8,9]), ("linear_barotropic_eos", [2,4,7,10]),
        ("absolute_pressure_positive_density", [1,2,6,7]), ("closed_mass_inventory", [1,2,3,6,7]),
        ("moving_wall_driving", [1,2,3,4,8]), ("body_acceleration", [6,7]),
        ("inner_boundary", [5,10]), ("nonuniform_initial_density_in_transient", [9]),
        ("bulk_viscosity_effects", [4,9]), ("open_inlet_density_and_full_traction_outlet", [5,8,9,10]),
        ("flow_rate_inlet", [5]), ("slip_symmetry_periodic", [4,6,8]),
    ],
    "lowmach_energy": [
        ("constant_transport_conduction_baseline", [1]), ("boussinesq_natural_convection", [2]),
        ("forced_convection_and_viscous_dissipation", [3]), ("mixed_aiding_and_opposing_convection", [4,5]),
        ("spatial_heat_source", [6]), ("outward_heat_flux_and_fixed_temperature", [7]),
        ("temperature_power_law_viscosity", [8]), ("temperature_power_law_conductivity", [9]),
        ("wall_partition_and_time_history", [10]), ("internal_thermal_boundary", [9]),
        ("volume_mean_gauge_including_hydrostatic_pressure", [2,4,5]),
        ("three_dimensional_nonplanar_driving", [3]),
    ],
    "euler_equilibrium": [
        ("strictly_zero_velocity_isentropic_branch", list(range(1,11))),
        ("constant_conservative_acceleration", [1,2,3,4]),
        ("spatially_varying_conservative_acceleration", [5,6,7,8,9,10]),
        ("geometry_dependent_total_mass_constraint", [4,7]),
        ("closed_slip_adiabatic_boundaries", list(range(1,11))),
        ("positive_state_and_temperature_bounds", list(range(1,11))),
        ("independent_entropy_parameter_and_mean_density", [4,10]),
    ],
    "euler_transient": [
        ("smooth_acoustics", [1,6]), ("nonlinear_compression_and_rarefaction", [2,3]),
        ("shock_and_entropy_admissibility", [4,7]), ("contact_discontinuity", [4,5]),
        ("multi_directional_waves", [6,7,8]), ("closed_wall_reflections", [8,10]),
        ("body_force_and_energy_conversion", [9]), ("inner_boundary", [10]),
        ("all_four_primary_fields_at_multiple_physical_times", list(range(1,11))),
        ("time_varying_body_acceleration", [9]),
    ],
    "compressible_energy": [
        ("ideal_gas_mass_inventory", [1,3]), ("thermal_and_mechanical_coupling", [2,4]),
        ("body_acceleration_and_stratification", [3]), ("viscous_dissipation", [4]),
        ("outward_heat_flux", [5]), ("inner_boundary_heating", [6]),
        ("spatial_heat_source", [7]), ("temperature_power_law_mu_and_k", [8]),
        ("independent_nonzero_bulk_viscosity", [9]), ("wall_temperature_partition_or_history", [10]),
        ("compression_work", [2,9]), ("nonuniform_physical_density_temperature_initial_state", [9]),
    ],
    "turbulent_flow": [
        ("single_and_multiple_wall_driving", [1,4,5,6]), ("aspect_ratio_and_recirculation", [2,3]),
        ("internal_boundaries_and_gap_flow", [7]), ("nonuniform_wall_partition", [8]),
        ("non_symmetric_momentum_input", [9]), ("transient_wall_history_or_steady_partition", [10]),
        ("pressure_representation_and_volume_gauge_or_closed_gas_mass", [1,2,7]),
        ("spatial_body_acceleration", [8]), ("urans_initial_k_and_integral_length_variation", [10]),
        ("resolved_discrete_sample_mean_covariance", [10]),
        ("fully_three_dimensional_cross_wall_flow", [6]),
    ],
    "free_surface": [
        ("dry_and_wet_downstream", [1,2]), ("free_surface_oscillation", [3,4]),
        ("multi_directional_and_asymmetric_motion", [4,5]), ("inner_fixed_boundaries", [6]),
        ("interacting_fronts", [7]), ("bed_step_geometry", [8]),
        ("viscosity_dominated_motion", [9]), ("connected_multibasin_geometry", [10]),
        ("liquid_only_dynamics_and_zero_gas_velocity_extension", list(range(1,11))),
        ("alpha_and_extended_velocity_pressure_true_cell_average", list(range(1,11))),
        ("nonzero_compatible_initial_velocity", [9]),
    ],
    "immiscible": [
        ("stable_and_unstable_density_order", [1,3]), ("lock_exchange", [2,10]),
        ("rising_and_sinking_phase", [4,5]), ("multiple_phase_regions", [6,10]),
        ("inclined_interface", [7]), ("inner_boundary", [8]),
        ("viscosity_contrast_and_nonzero_initial_velocity", [9]),
        ("both_phases_momentum_zero_surface_tension", list(range(1,11))),
        ("velocity_continuity_and_traction_continuity", list(range(1,11))),
    ],
    "capillary": [
        ("laplace_pressure_and_gauge", [1]), ("advancing_and_receding_contact_lines", [2,3]),
        ("corner_and_internal_wall_wetting", [4,8]), ("liquid_bridge", [5]),
        ("capillary_viscous_relaxation", [6]), ("gravity_capillary_competition", [7]),
        ("multiple_interfaces", [9]), ("anisotropic_shape", [10]),
        ("physical_navier_slip_not_mesh_slip", [2,3,4,5]),
        ("wetting_neutral_nonwetting_contact_angles_across_cases", [1,2,3,4]),
        ("vary_density_and_viscosity_ratios_with_meaning", [6,7]),
    ],
    "dispersed": [
        ("drag_relaxation", [1,5,6]), ("settling_or_rising", [2,9]),
        ("multiple_clouds", [3]), ("inertial_motion_in_carrier_vortex", [4]),
        ("inhomogeneous_volume_fraction_transport", [7]), ("inner_wall_boundary", [8]),
        ("spatial_slip_and_pressure_feedback", [10]), ("superficial_flux_not_conditional_velocity", list(range(1,11))),
        ("exact_zero_missing_phase_flux", [2]),
        ("dense_crowding_pressure_and_viscosity_when_applicable", [7,10]),
        ("matching_one_way_two_way_and_phase_stresses", list(range(1,11))),
    ],
    "exchange": [
        ("two_temperature_exchange", [1]), ("two_concentration_exchange", [2]),
        ("combined_different_relaxation_times", [3]), ("wall_conduction", [4]),
        ("diffusion_exchange_competition", [5]), ("advective_exchange", [6]),
        ("variable_phase_fraction_weighting", [7]), ("inner_thermal_boundary", [8]),
        ("spatially_separated_thermal_solute_patterns", [9]), ("time_varying_wall_temperature", [10]),
        ("phase_volume_weighted_conservation_and_partition_coefficient_one", list(range(1,11))),
    ],
    "evaporation": [
        ("positive_and_negative_mass_transfer", [1,2]), ("sensible_and_latent_enthalpy_jump", [3]),
        ("curved_and_offcentre_interfaces", [4,5]), ("vapour_pocket_condensation", [6]),
        ("multiple_interfaces", [7]), ("gravity_and_recoil", [8]),
        ("evaporation_condensation_switch", [9]), ("inner_boundary", [10]),
        ("normal_velocity_jump_and_recoil_traction", list(range(1,11))),
        ("interface_integral_to_cell_average_mass_rate", list(range(1,11))),
        ("unequal_phase_heat_capacities", [3]),
    ],
    "boiling": [
        ("pure_liquid_bulk_nucleation", [1]), ("bulk_condensation", [2]),
        ("bottom_and_side_thermal_driving", [3,4]), ("localized_superheat_subcooling", [5,6]),
        ("initial_fraction_and_temperature_variation", [7]), ("phase_change_reversal", [8]),
        ("inner_thermal_boundary", [9]), ("reservoir_backflow_phase_state", [10]),
        ("divergence_from_phase_change_and_deviatoric_stress", list(range(1,11))),
        ("complete_mixture_enthalpy_without_double_latent_source", list(range(1,11))),
    ],
    "cavitation": [
        ("linear_pressure_evaporation", [1]), ("nuclei_limited_condensation", [2]),
        ("body_force_driven_pressure_gradient", [3,4]), ("localized_phase_fraction", [5,6]),
        ("inner_boundary_pressure_minimum", [7]), ("multiple_vapour_regions", [8]),
        ("time_dependent_force_and_recovery", [9]), ("reservoir_fraction_history", [10]),
        ("nonzero_divergence_and_correct_deviatoric_stress", list(range(1,11))),
        ("absolute_pressure_relative_to_saturation", list(range(1,11))),
    ],
    "melting": [
        ("melting_and_freezing_sign", [1,2]), ("interacting_phase_fronts", [3]),
        ("multidirectional_front_and_thermal_boundary", [4,5,10]), ("inner_boundary", [6]),
        ("initial_mushy_zone", [7]), ("thermal_history_reversal", [8]),
        ("nonzero_initial_velocity_and_material_derivative_rate", [9]),
        ("finite_mushy_damping_not_immobile_solid_constraint", [7,9]),
        ("alpha_uniquely_from_temperature", list(range(1,11))),
    ],
    "liquid_film": [
        ("load_generation", [1]), ("cavitation_and_reformation", [2,3]),
        ("two_dimensional_side_leakage", [4]), ("oblique_vector_transport", [5]),
        ("independent_two_wall_motion", [6]), ("spatial_gap_texture", [7]),
        ("pressure_driven_flow", [8]), ("starvation_inlet_fraction", [9]),
        ("inner_pressure_boundary", [10]), ("elrod_adams_complementarity_and_mass_flux", [2,3,9]),
        ("load_integral_and_film_fraction", [1,2,3,8,9]),
    ],
    "gas_film": [
        ("squeeze_and_separation", [1,2]), ("wall_driven_transient_pumping", [3]),
        ("boundary_pressure_history", [4]), ("spatiotemporal_gap", [5]),
        ("spatial_texture", [6]), ("two_dimensional_vector_flux", [7]),
        ("independent_wall_velocity_histories", [8]), ("inner_pressure_boundary", [9]),
        ("squeeze_release_switch", [10]), ("isothermal_density_pressure_coupling", list(range(1,11))),
        ("one_sided_gap_time_derivative_at_knots", [1,2,5,10]),
    ],
    "thermal_film": [
        ("pressure_and_shear_dissipation", [1,2,3]), ("squeeze_term", [4]),
        ("spatial_wall_temperature", [5]), ("weak_strong_two_wall_heat_exchange", [6,7]),
        ("exponential_temperature_viscosity_feedback", [8]), ("wall_thermal_history", [9]),
        ("inner_pressure_and_temperature_boundary", [10]),
        ("cross_gap_uniform_temperature_closure", list(range(1,11))),
        ("side_dirichlet_temperature_including_outflow", list(range(1,11))),
    ],
    "nonnewtonian_film": [
        ("uniform_couette_shear_baseline", [1]), ("cross_gap_variable_shear", [2]),
        ("combined_couette_poiseuille_cross_gap_bvp", [3,9]), ("converging_diverging_full_film", [4,5]),
        ("two_dimensional_side_leakage", [6]), ("vector_cross_gap_response", [7]),
        ("spatial_gap_texture", [8]), ("inner_pressure_boundary", [10]),
        ("carreau_plateaus_and_transition_with_actual_local_shear", [2,3]),
        ("no_effective_newtonian_substitution", list(range(1,11))),
    ],
    "shallow_steady": [
        ("subcritical_reservoir_flow", [1]), ("bed_bump_trough_and_cross_slope", [2,3,4]),
        ("geometric_contraction_expansion", [5,6]), ("island_boundary", [7]),
        ("linear_bed_friction", [8]), ("two_dimensional_discharge", [9]),
        ("multiple_bed_features", [10]), ("characteristic_reservoir_not_full_dirichlet", list(range(1,11))),
        ("unique_truly_steady_positive_depth_state", list(range(1,11))),
        ("supercritical_inlet_controlled_unique_branch", [6]),
    ],
    "shallow_transient": [
        ("smooth_gravity_waves", [1,4]), ("wet_bed_shock_rarefaction", [2]),
        ("radial_and_crossing_waves", [3,7]), ("nonflat_bed_source", [5,10]),
        ("island_diffraction", [6]), ("linear_drag_decay", [8]),
        ("reservoir_history", [9]), ("positive_depth_and_entropy_weak_solution", [2,3,7]),
        ("depth_velocity_and_volume_integral", list(range(1,11))),
    ],
    "wetdry": [
        ("initial_dry_bed", [1,2]), ("runup_and_retreat", [3]),
        ("bed_obstacle_overtopping", [4]), ("island_front_splitting", [5]),
        ("colliding_wetting_fronts", [6]), ("reservoir_flood_history", [7]),
        ("drainage_and_residual_pools", [8]), ("linear_drag", [9]),
        ("compound_bed_and_branching", [10]), ("dry_state_and_zero_velocity_observation_convention", list(range(1,11))),
    ],
    "two_layer": [
        ("external_and_internal_wave_modes", [1,2]), ("counterflow_and_codirectional_shear", [3,4]),
        ("nonflat_bed", [5]), ("two_dimensional_layer_flux", [6]),
        ("bed_and_interface_drag_distinct", [7,8]), ("inner_boundary", [9]),
        ("interacting_layer_modes", [10]), ("smooth_positive_depth_hyperbolic_stable_scope", list(range(1,11))),
        ("full_supercritical_layer_inlet_and_outflow", [10]),
    ],
    "slip_gas": [
        ("pressure_and_couette_driving", [1,2]), ("aiding_and_opposing_drive", [3,4]),
        ("geometry_contraction_expansion", [5,6]), ("inner_boundary", [7]),
        ("curved_microchannel", [8]), ("asymmetric_walls", [9]), ("multiple_reservoirs", [10]),
        ("hard_sphere_viscosity_and_absolute_pressure", list(range(1,11))),
        ("navier_slip_and_no_penetration", list(range(1,11))),
        ("thermal_jump_and_heat_transport_if_thermal", [8,9]),
        ("all_legal_wall_inlet_outlet_operators", [1,2,8,9,10]),
    ],
    "kinetic_gas": [
        ("pressure_driven_nonequilibrium", [1]), ("different_reservoir_temperatures", [2]),
        ("moving_wall", [3]), ("partial_maxwell_accommodation", [4]),
        ("orifice_and_shadow_transport", [5,7]), ("bent_trajectory_history", [6]),
        ("hot_cold_wall_reemission", [8]), ("multiple_halfspace_reservoirs", [9]),
        ("pure_specular_diffuse_mixed_wall_partitions", [10]),
        ("hard_sphere_collisions_or_exact_collisionless_branch", list(range(1,11))),
        ("full_three_velocity_moments", list(range(1,11))),
    ],
    "viscoelastic": [
        ("oldroyd_b_coupled_momentum_and_conformation", [1,2]), ("opposed_wall_shear", [3]),
        ("extensional_stagnation_flow", [4]), ("internal_obstacle_transport", [5]),
        ("asymmetric_driving", [6,8]), ("codirectional_driving", [7]),
        ("relaxation_and_reversal_or_steady_multisegment_drive", [9,10]),
        ("nonidentity_spd_initial_conformation_if_transient", [8]),
        ("inflow_conformation_and_natural_memory_outflow", [7]),
        ("full_vector_traction_and_pressure_convention", [7]),
        ("polymer_stress_and_A_not_only_u_p", list(range(1,11))),
    ],
    "thixotropic": [
        ("structure_breakdown_and_rebuild", [1,2]), ("reversal_hysteresis", [3]),
        ("opposed_shear", [4]), ("spatial_structure_transport", [5,6,7]),
        ("intermittent_rest", [8]), ("history_interaction", [9,10]),
        ("linear_structure_viscosity_and_build_break_kinetics", list(range(1,11))),
        ("inlet_structure_and_natural_outflow", [9,10]),
        ("traction_outlet_and_absolute_pressure_convention", [9,10]),
    ],
    "thermal_generalized": [
        ("temperature_shifted_carreau_not_power_law_T", [1,2]),
        ("shear_dissipation_and_temperature_feedback", [3,8]),
        ("multiple_mechanical_and_thermal_partitions", [4,7]),
        ("fully_3d_cross_wall_motion", [5]), ("inner_thermal_boundary", [6]),
        ("temperature_history_and_reversal", [9,10]),
        ("velocity_inlet_full_traction_outlet_and_thermal_dirichlet", [4]),
        ("no_boussinesq_expansion_or_undeclared_heat_source", list(range(1,11))),
        ("all_dirichlet_thermal_boundaries_and_pressure_gauge", list(range(1,11))),
        ("carreau_plateau_transition_not_only_single_effective_mu", [3,8]),
    ],
}


def matrix(family, entries, slug):
    result=[]
    for key, indices in FEATURES[family]:
        if "three_dimensional" in key and not(slug.endswith("3d") or slug=="thermal-generalized-newtonian"):
            continue
        if key=="urans_initial_k_and_integral_length_variation" and "urans" not in slug:
            continue
        if key=="resolved_discrete_sample_mean_covariance" and "statistics" not in slug:
            continue
        if key=="nonidentity_spd_initial_conformation_if_transient" and slug=="viscoelastic-steady":
            continue
        if key=="thermal_jump_and_heat_transport_if_thermal" and slug=="isothermal-slip":
            continue
        result.append({"requirement":key,"assigned_design_ids":[entries[i-1]["design_id"] for i in indices],
                       "status":"planned_not_implemented" if indices else "design_gap",
                       "implementation_evidence":[]})
    if slug=="thermal-viscoelastic":
        result += [{"requirement":k,"assigned_design_ids":[entries[i-1]["design_id"] for i in indices],"status":"planned_not_implemented","implementation_evidence":[]} for k,indices in (
            ("coupled_temperature_shift_of_eta_s_eta_p_lambda",[1,3,6]),
            ("conformation_free_energy_relaxation_heat_not_all_tau_p_work",[8,9]),
            ("thermal_initial_boundary_histories_and_thermal_advection",[7,10]))]
    return result


def representation_targets(section, dimension):
    """Targets requiring later concrete mesh/array choices, not numerical claims."""
    common=[
        "实体tag作为身份而非数组行号；位置与字段显式引用；输出轴及IDs原样返回",
        "全部必需主字段；在有唯一物理迹处选择本题允许的适用派生/整体观测",
        "真实几何网格、合法边界不重不漏；不把二维结果简单挤出充当三维响应" if dimension==3 else "全局xy真实几何；按本题定义区分单位厚度与实际水平面积",
        "在输入预算内选择基线、耦合及较复杂工况；复杂度不能只来自扩大网格或延长时域",
    ]
    if section.startswith("2.1-"):
        common += ["在十例间安排point、cell average、region mean及真实边界积分；不在奇异角点请求导数",
                   "二维安排三角/四边形及合法混合网格；三维安排四面体、六面体及有意义的棱柱/金字塔过渡网格",
                   "初态、边界历史、体源历史使用各自明确的采样轴；请求输出时刻不决定内部步长"]
    elif section.startswith(("2.2-","2.3-","2.4-","2.5-","2.6-","2.7-")):
        common += ["全部域单元的面积/体积平均主字段；不把节点插值冒充单元平均",
                   "二维与三维按各题允许的一阶单元类型安排网格；时间、参数和字段不添加求解器私有输入"]
    else:
        common += ["一阶单纯形网格与节点分片线性输入；输出采用本题允许的真实节点子集，避开多迹或非唯一导数位置",
                   "整体量仅使用本题允许的aggregate/source；不制造带坐标的汇总探针"]
    return [{"target":x,"status":"not_yet_instantiated_in_input","case_assignment":"to_be_fixed_with_mesh_and_observation_design"} for x in common]
