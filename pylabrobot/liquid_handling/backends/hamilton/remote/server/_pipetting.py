"""RPC handlers for pipetting operations (tips, aspirate, dispense, probing)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pylabrobot.liquid_handling.backends.hamilton.STAR_backend import STARBackend
from pylabrobot.resources.hamilton import TipDropMethod, TipPickupMethod, TipSize

from .. import star_service_pb2 as pb2
from ..helpers import (
    aspiration_from_proto,
    coordinate_from_proto,
    dispense_from_proto,
    drop_from_proto,
    drop_tip_rack_from_proto,
    extract_optional_field,
    extract_optional_list,
    multi_head_aspiration_container_from_proto,
    multi_head_aspiration_plate_from_proto,
    multi_head_dispense_container_from_proto,
    multi_head_dispense_plate_from_proto,
    pickup_from_proto,
    pickup_tip_rack_from_proto,
)

if TYPE_CHECKING:
    from connectrpc.request import RequestContext


# ---------------------------------------------------------------------------
# Enum mappings
# ---------------------------------------------------------------------------

_PROTO_TO_TIP_SIZE = {
    pb2.TIP_SIZE_UNDEFINED: TipSize.UNDEFINED,
    pb2.LOW_VOLUME: TipSize.LOW_VOLUME,
    pb2.STANDARD_VOLUME: TipSize.STANDARD_VOLUME,
    pb2.HIGH_VOLUME: TipSize.HIGH_VOLUME,
    pb2.CORE_384: TipSize.CORE_384_HEAD_TIP,
    pb2.XL: TipSize.XL,
}

_PROTO_TO_PICKUP_METHOD = {
    pb2.OUT_OF_RACK: TipPickupMethod.OUT_OF_RACK,
    pb2.OUT_OF_WASH_LIQUID: TipPickupMethod.OUT_OF_WASH_LIQUID,
}

_PROTO_TO_DROP_METHOD = {
    pb2.PLACE_SHIFT: TipDropMethod.PLACE_SHIFT,
    pb2.TIP_DROP: TipDropMethod.DROP,
}


class PipettingServerMixin:
    """RPC handlers for pipetting operations.

    ``self._backend`` is a :class:`STARBackend` instance (set by ``__init__.py``).
    """

    # ===================================================================
    # High-level tip handling
    # ===================================================================

    async def pick_up_tips(
        self, request: pb2.PickUpTipsRequest, ctx: RequestContext
    ) -> pb2.PickUpTipsResponse:
        ops = [pickup_from_proto(self._backend.deck, op) for op in request.ops]
        use_channels = list(request.use_channels)
        kwargs: dict = {}
        begin = extract_optional_field(request, "begin_tip_pick_up_process")
        if begin is not None:
            kwargs["begin_tip_pick_up_process"] = begin
        end = extract_optional_field(request, "end_tip_pick_up_process")
        if end is not None:
            kwargs["end_tip_pick_up_process"] = end
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        pm = extract_optional_field(request, "pickup_method")
        if pm is not None:
            kwargs["pickup_method"] = TipPickupMethod(pm)
        await self._backend.pick_up_tips(
            ops=ops,
            use_channels=use_channels,
            **kwargs,
        )
        return pb2.PickUpTipsResponse()

    async def drop_tips(
        self, request: pb2.DropTipsRequest, ctx: RequestContext
    ) -> pb2.DropTipsResponse:
        ops = [drop_from_proto(self._backend.deck, op) for op in request.ops]
        use_channels = list(request.use_channels)
        kwargs: dict = {}
        dm = extract_optional_field(request, "drop_method")
        if dm is not None:
            kwargs["drop_method"] = _PROTO_TO_DROP_METHOD[dm]
        begin = extract_optional_field(request, "begin_tip_deposit_process")
        if begin is not None:
            kwargs["begin_tip_deposit_process"] = begin
        end = extract_optional_field(request, "end_tip_deposit_process")
        if end is not None:
            kwargs["end_tip_deposit_process"] = end
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        z_end = extract_optional_field(request, "z_position_at_end_of_a_command")
        if z_end is not None:
            kwargs["z_position_at_end_of_a_command"] = z_end
        await self._backend.drop_tips(
            ops=ops,
            use_channels=use_channels,
            **kwargs,
        )
        return pb2.DropTipsResponse()

    # ===================================================================
    # High-level aspirate / dispense
    # ===================================================================

    async def aspirate(
        self, request: pb2.AspirateRequest, ctx: RequestContext
    ) -> pb2.AspirateResponse:
        ops = [aspiration_from_proto(self._backend.deck, op) for op in request.ops]
        use_channels = list(request.use_channels)
        kwargs: dict = {}

        jet = extract_optional_list(request, "jet")
        if jet is not None:
            kwargs["jet"] = jet
        blow_out = extract_optional_list(request, "blow_out")
        if blow_out is not None:
            kwargs["blow_out"] = blow_out
        lld_search_height = extract_optional_list(request, "lld_search_height")
        if lld_search_height is not None:
            kwargs["lld_search_height"] = lld_search_height
        clot_detection_height = extract_optional_list(request, "clot_detection_height")
        if clot_detection_height is not None:
            kwargs["clot_detection_height"] = clot_detection_height
        pull_out = extract_optional_list(request, "pull_out_distance_transport_air")
        if pull_out is not None:
            kwargs["pull_out_distance_transport_air"] = pull_out
        ssh = extract_optional_list(request, "second_section_height")
        if ssh is not None:
            kwargs["second_section_height"] = ssh
        ssr = extract_optional_list(request, "second_section_ratio")
        if ssr is not None:
            kwargs["second_section_ratio"] = ssr
        mh = extract_optional_list(request, "minimum_height")
        if mh is not None:
            kwargs["minimum_height"] = mh
        imm = extract_optional_list(request, "immersion_depth")
        if imm is not None:
            kwargs["immersion_depth"] = imm
        sfd = extract_optional_list(request, "surface_following_distance")
        if sfd is not None:
            kwargs["surface_following_distance"] = sfd
        tav = extract_optional_list(request, "transport_air_volume")
        if tav is not None:
            kwargs["transport_air_volume"] = tav
        pwv = extract_optional_list(request, "pre_wetting_volume")
        if pwv is not None:
            kwargs["pre_wetting_volume"] = pwv
        lld_mode = extract_optional_list(request, "lld_mode")
        if lld_mode is not None:
            kwargs["lld_mode"] = [STARBackend.LLDMode(m) for m in lld_mode]
        glld = extract_optional_list(request, "gamma_lld_sensitivity")
        if glld is not None:
            kwargs["gamma_lld_sensitivity"] = glld
        dplld = extract_optional_list(request, "dp_lld_sensitivity")
        if dplld is not None:
            kwargs["dp_lld_sensitivity"] = dplld
        apz = extract_optional_list(request, "aspirate_position_above_z_touch_off")
        if apz is not None:
            kwargs["aspirate_position_above_z_touch_off"] = apz
        dhd = extract_optional_list(
            request, "detection_height_difference_for_dual_lld"
        )
        if dhd is not None:
            kwargs["detection_height_difference_for_dual_lld"] = dhd
        ss = extract_optional_list(request, "swap_speed")
        if ss is not None:
            kwargs["swap_speed"] = ss
        st = extract_optional_list(request, "settling_time")
        if st is not None:
            kwargs["settling_time"] = st
        mpls = extract_optional_list(request, "mix_position_from_liquid_surface")
        if mpls is not None:
            kwargs["mix_position_from_liquid_surface"] = mpls
        msfd = extract_optional_list(request, "mix_surface_following_distance")
        if msfd is not None:
            kwargs["mix_surface_following_distance"] = msfd
        lci = extract_optional_list(request, "limit_curve_index")
        if lci is not None:
            kwargs["limit_curve_index"] = lci
        u2sa = extract_optional_list(request, "use_2nd_section_aspiration")
        if u2sa is not None:
            kwargs["use_2nd_section_aspiration"] = u2sa
        rh2s = extract_optional_list(
            request, "retract_height_over_2nd_section_to_empty_tip"
        )
        if rh2s is not None:
            kwargs["retract_height_over_2nd_section_to_empty_tip"] = rh2s
        dsdet = extract_optional_list(
            request, "dispensation_speed_during_emptying_tip"
        )
        if dsdet is not None:
            kwargs["dispensation_speed_during_emptying_tip"] = dsdet
        ddsd2ss = extract_optional_list(
            request, "dosing_drive_speed_during_2nd_section_search"
        )
        if ddsd2ss is not None:
            kwargs["dosing_drive_speed_during_2nd_section_search"] = ddsd2ss
        zdsd2ss = extract_optional_list(
            request, "z_drive_speed_during_2nd_section_search"
        )
        if zdsd2ss is not None:
            kwargs["z_drive_speed_during_2nd_section_search"] = zdsd2ss
        cue = extract_optional_list(request, "cup_upper_edge")
        if cue is not None:
            kwargs["cup_upper_edge"] = cue
        rlr = extract_optional_list(request, "ratio_liquid_rise_to_tip_deep_in")
        if rlr is not None:
            kwargs["ratio_liquid_rise_to_tip_deep_in"] = rlr
        id2 = extract_optional_list(request, "immersion_depth_2nd_section")
        if id2 is not None:
            kwargs["immersion_depth_2nd_section"] = id2
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        mze = extract_optional_field(request, "min_z_endpos")
        if mze is not None:
            kwargs["min_z_endpos"] = mze
        lsnl = extract_optional_list(request, "liquid_surface_no_lld")
        if lsnl is not None:
            kwargs["liquid_surface_no_lld"] = lsnl
        dvc = extract_optional_list(request, "disable_volume_correction")
        if dvc is not None:
            kwargs["disable_volume_correction"] = dvc

        kwargs["probe_liquid_height"] = request.probe_liquid_height
        kwargs["auto_surface_following_distance"] = (
            request.auto_surface_following_distance
        )

        await self._backend.aspirate(
            ops=ops,
            use_channels=use_channels,
            **kwargs,
        )
        return pb2.AspirateResponse()

    async def dispense(
        self, request: pb2.DispenseRequest, ctx: RequestContext
    ) -> pb2.DispenseResponse:
        ops = [dispense_from_proto(self._backend.deck, op) for op in request.ops]
        use_channels = list(request.use_channels)
        kwargs: dict = {}

        lsh = extract_optional_list(request, "lld_search_height")
        if lsh is not None:
            kwargs["lld_search_height"] = lsh
        lsnl = extract_optional_list(request, "liquid_surface_no_lld")
        if lsnl is not None:
            kwargs["liquid_surface_no_lld"] = lsnl
        pull_out = extract_optional_list(request, "pull_out_distance_transport_air")
        if pull_out is not None:
            kwargs["pull_out_distance_transport_air"] = pull_out
        ssh = extract_optional_list(request, "second_section_height")
        if ssh is not None:
            kwargs["second_section_height"] = ssh
        ssr = extract_optional_list(request, "second_section_ratio")
        if ssr is not None:
            kwargs["second_section_ratio"] = ssr
        mh = extract_optional_list(request, "minimum_height")
        if mh is not None:
            kwargs["minimum_height"] = mh
        imm = extract_optional_list(request, "immersion_depth")
        if imm is not None:
            kwargs["immersion_depth"] = imm
        sfd = extract_optional_list(request, "surface_following_distance")
        if sfd is not None:
            kwargs["surface_following_distance"] = sfd
        cos = extract_optional_list(request, "cut_off_speed")
        if cos is not None:
            kwargs["cut_off_speed"] = cos
        sbv = extract_optional_list(request, "stop_back_volume")
        if sbv is not None:
            kwargs["stop_back_volume"] = sbv
        tav = extract_optional_list(request, "transport_air_volume")
        if tav is not None:
            kwargs["transport_air_volume"] = tav
        lld_mode = extract_optional_list(request, "lld_mode")
        if lld_mode is not None:
            kwargs["lld_mode"] = [STARBackend.LLDMode(m) for m in lld_mode]
        dpz = extract_optional_list(request, "dispense_position_above_z_touch_off")
        if dpz is not None:
            kwargs["dispense_position_above_z_touch_off"] = dpz
        glld = extract_optional_list(request, "gamma_lld_sensitivity")
        if glld is not None:
            kwargs["gamma_lld_sensitivity"] = glld
        dplld = extract_optional_list(request, "dp_lld_sensitivity")
        if dplld is not None:
            kwargs["dp_lld_sensitivity"] = dplld
        ss = extract_optional_list(request, "swap_speed")
        if ss is not None:
            kwargs["swap_speed"] = ss
        st = extract_optional_list(request, "settling_time")
        if st is not None:
            kwargs["settling_time"] = st
        mpls = extract_optional_list(request, "mix_position_from_liquid_surface")
        if mpls is not None:
            kwargs["mix_position_from_liquid_surface"] = mpls
        msfd = extract_optional_list(request, "mix_surface_following_distance")
        if msfd is not None:
            kwargs["mix_surface_following_distance"] = msfd
        lci = extract_optional_list(request, "limit_curve_index")
        if lci is not None:
            kwargs["limit_curve_index"] = lci
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        mze = extract_optional_field(request, "min_z_endpos")
        if mze is not None:
            kwargs["min_z_endpos"] = mze

        kwargs["side_touch_off_distance"] = request.side_touch_off_distance

        jet = extract_optional_list(request, "jet")
        if jet is not None:
            kwargs["jet"] = jet
        blow_out = extract_optional_list(request, "blow_out")
        if blow_out is not None:
            kwargs["blow_out"] = blow_out
        empty = extract_optional_list(request, "empty")
        if empty is not None:
            kwargs["empty"] = empty
        dvc = extract_optional_list(request, "disable_volume_correction")
        if dvc is not None:
            kwargs["disable_volume_correction"] = dvc

        kwargs["probe_liquid_height"] = request.probe_liquid_height
        kwargs["auto_surface_following_distance"] = (
            request.auto_surface_following_distance
        )

        await self._backend.dispense(
            ops=ops,
            use_channels=use_channels,
            **kwargs,
        )
        return pb2.DispenseResponse()

    # ===================================================================
    # 96-head tip handling
    # ===================================================================

    async def pick_up_tips96(
        self, request: pb2.PickUpTips96Request, ctx: RequestContext
    ) -> pb2.PickUpTips96Response:
        pickup = pickup_tip_rack_from_proto(self._backend.deck, request.pickup)
        kwargs: dict = {}
        if request.tip_pickup_method:
            kwargs["tip_pickup_method"] = request.tip_pickup_method
        mhce = extract_optional_field(request, "minimum_height_command_end")
        if mhce is not None:
            kwargs["minimum_height_command_end"] = mhce
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        if request.experimental_alignment_tipspot_identifier:
            kwargs["experimental_alignment_tipspot_identifier"] = (
                request.experimental_alignment_tipspot_identifier
            )
        await self._backend.pick_up_tips96(pickup=pickup, **kwargs)
        return pb2.PickUpTips96Response()

    async def drop_tips96(
        self, request: pb2.DropTips96Request, ctx: RequestContext
    ) -> pb2.DropTips96Response:
        drop = drop_tip_rack_from_proto(self._backend.deck, request.drop)
        kwargs: dict = {}
        mhce = extract_optional_field(request, "minimum_height_command_end")
        if mhce is not None:
            kwargs["minimum_height_command_end"] = mhce
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        if request.experimental_alignment_tipspot_identifier:
            kwargs["experimental_alignment_tipspot_identifier"] = (
                request.experimental_alignment_tipspot_identifier
            )
        await self._backend.drop_tips96(drop=drop, **kwargs)
        return pb2.DropTips96Response()

    # ===================================================================
    # 96-head aspirate / dispense
    # ===================================================================

    async def aspirate96(
        self, request: pb2.Aspirate96Request, ctx: RequestContext
    ) -> pb2.Aspirate96Response:
        aspiration_variant = request.WhichOneof("aspiration")
        if aspiration_variant == "plate":
            aspiration = multi_head_aspiration_plate_from_proto(
                self._backend.deck, request.plate
            )
        else:
            aspiration = multi_head_aspiration_container_from_proto(
                self._backend.deck, request.container
            )

        kwargs: dict = {}
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        mze = extract_optional_field(request, "min_z_endpos")
        if mze is not None:
            kwargs["min_z_endpos"] = mze
        mh = extract_optional_field(request, "minimum_height")
        if mh is not None:
            kwargs["minimum_height"] = mh

        await self._backend.aspirate96(
            aspiration=aspiration,
            jet=request.jet,
            blow_out=request.blow_out,
            use_lld=request.use_lld,
            pull_out_distance_transport_air=request.pull_out_distance_transport_air,
            aspiration_type=request.aspiration_type,
            lld_search_height=request.lld_search_height,
            second_section_height=request.second_section_height,
            second_section_ratio=request.second_section_ratio,
            immersion_depth=request.immersion_depth,
            surface_following_distance=request.surface_following_distance,
            transport_air_volume=request.transport_air_volume,
            pre_wetting_volume=request.pre_wetting_volume,
            gamma_lld_sensitivity=request.gamma_lld_sensitivity,
            swap_speed=request.swap_speed,
            settling_time=request.settling_time,
            mix_position_from_liquid_surface=request.mix_position_from_liquid_surface,
            mix_surface_following_distance=request.mix_surface_following_distance,
            limit_curve_index=request.limit_curve_index,
            disable_volume_correction=request.disable_volume_correction,
            **kwargs,
        )
        return pb2.Aspirate96Response()

    async def dispense96(
        self, request: pb2.Dispense96Request, ctx: RequestContext
    ) -> pb2.Dispense96Response:
        dispense_variant = request.WhichOneof("dispense_op")
        if dispense_variant == "plate":
            dispense_op = multi_head_dispense_plate_from_proto(
                self._backend.deck, request.plate
            )
        else:
            dispense_op = multi_head_dispense_container_from_proto(
                self._backend.deck, request.container
            )

        kwargs: dict = {}
        mth = extract_optional_field(
            request, "minimum_traverse_height_at_beginning_of_a_command"
        )
        if mth is not None:
            kwargs["minimum_traverse_height_at_beginning_of_a_command"] = mth
        mze = extract_optional_field(request, "min_z_endpos")
        if mze is not None:
            kwargs["min_z_endpos"] = mze
        mh = extract_optional_field(request, "minimum_height")
        if mh is not None:
            kwargs["minimum_height"] = mh

        await self._backend.dispense96(
            dispense=dispense_op,
            jet=request.jet,
            empty=request.empty,
            blow_out=request.blow_out,
            pull_out_distance_transport_air=request.pull_out_distance_transport_air,
            use_lld=request.use_lld,
            lld_search_height=request.lld_search_height,
            second_section_height=request.second_section_height,
            second_section_ratio=request.second_section_ratio,
            immersion_depth=request.immersion_depth,
            surface_following_distance=request.surface_following_distance,
            transport_air_volume=request.transport_air_volume,
            gamma_lld_sensitivity=request.gamma_lld_sensitivity,
            swap_speed=request.swap_speed,
            settling_time=request.settling_time,
            mix_position_from_liquid_surface=request.mix_position_from_liquid_surface,
            mix_surface_following_distance=request.mix_surface_following_distance,
            limit_curve_index=request.limit_curve_index,
            cut_off_speed=request.cut_off_speed,
            stop_back_volume=request.stop_back_volume,
            disable_volume_correction=request.disable_volume_correction,
            **kwargs,
        )
        return pb2.Dispense96Response()

    # ===================================================================
    # Low-level firmware: initialization
    # ===================================================================

    async def initialize_pip(
        self, request: pb2.InitializePipRequest, ctx: RequestContext
    ) -> pb2.InitializePipResponse:
        await self._backend.initialize_pip()
        return pb2.InitializePipResponse()

    async def initialize_pipetting_channels(
        self,
        request: pb2.InitializePipettingChannelsRequest,
        ctx: RequestContext,
    ) -> pb2.InitializePipettingChannelsResponse:
        await self._backend.initialize_pipetting_channels(
            x_positions=list(request.x_positions),
            y_positions=list(request.y_positions),
            begin_of_tip_deposit_process=request.begin_of_tip_deposit_process,
            end_of_tip_deposit_process=request.end_of_tip_deposit_process,
            z_position_at_end_of_a_command=request.z_position_at_end_of_a_command,
            tip_pattern=list(request.tip_pattern),
            tip_type=request.tip_type,
            discarding_method=request.discarding_method,
        )
        return pb2.InitializePipettingChannelsResponse()

    # ===================================================================
    # Low-level firmware: tip pick up / discard
    # ===================================================================

    async def pick_up_tip_fw(
        self, request: pb2.PickUpTipFwRequest, ctx: RequestContext
    ) -> pb2.PickUpTipFwResponse:
        await self._backend.pick_up_tip(
            x_positions=list(request.x_positions),
            y_positions=list(request.y_positions),
            tip_pattern=list(request.tip_pattern),
            tip_type_idx=request.tip_type_idx,
            begin_tip_pick_up_process=request.begin_tip_pick_up_process,
            end_tip_pick_up_process=request.end_tip_pick_up_process,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            pickup_method=TipPickupMethod(request.pickup_method),
        )
        return pb2.PickUpTipFwResponse()

    async def discard_tip_fw(
        self, request: pb2.DiscardTipFwRequest, ctx: RequestContext
    ) -> pb2.DiscardTipFwResponse:
        await self._backend.discard_tip(
            x_positions=list(request.x_positions),
            y_positions=list(request.y_positions),
            tip_pattern=list(request.tip_pattern),
            begin_tip_deposit_process=request.begin_tip_deposit_process,
            end_tip_deposit_process=request.end_tip_deposit_process,
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            z_position_at_end_of_a_command=request.z_position_at_end_of_a_command,
            discarding_method=TipDropMethod(request.discarding_method),
        )
        return pb2.DiscardTipFwResponse()

    # ===================================================================
    # Low-level firmware: aspirate_pip / dispense_pip
    # ===================================================================

    async def aspirate_pip(
        self, request: pb2.AspiratePipRequest, ctx: RequestContext
    ) -> pb2.AspiratePipResponse:
        await self._backend.aspirate_pip(
            aspiration_type=list(request.aspiration_type),
            tip_pattern=list(request.tip_pattern),
            x_positions=list(request.x_positions),
            y_positions=list(request.y_positions),
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            min_z_endpos=request.min_z_endpos,
            lld_search_height=list(request.lld_search_height),
            clot_detection_height=list(request.clot_detection_height),
            liquid_surface_no_lld=list(request.liquid_surface_no_lld),
            pull_out_distance_transport_air=list(request.pull_out_distance_transport_air),
            second_section_height=list(request.second_section_height),
            second_section_ratio=list(request.second_section_ratio),
            minimum_height=list(request.minimum_height),
            immersion_depth=list(request.immersion_depth),
            immersion_depth_direction=list(request.immersion_depth_direction),
            surface_following_distance=list(request.surface_following_distance),
            aspiration_volumes=list(request.aspiration_volumes),
            aspiration_speed=list(request.aspiration_speed),
            transport_air_volume=list(request.transport_air_volume),
            blow_out_air_volume=list(request.blow_out_air_volume),
            pre_wetting_volume=list(request.pre_wetting_volume),
            lld_mode=list(request.lld_mode),
            gamma_lld_sensitivity=list(request.gamma_lld_sensitivity),
            dp_lld_sensitivity=list(request.dp_lld_sensitivity),
            aspirate_position_above_z_touch_off=list(
                request.aspirate_position_above_z_touch_off
            ),
            detection_height_difference_for_dual_lld=list(
                request.detection_height_difference_for_dual_lld
            ),
            swap_speed=list(request.swap_speed),
            settling_time=list(request.settling_time),
            mix_volume=list(request.mix_volume),
            mix_cycles=list(request.mix_cycles),
            mix_position_from_liquid_surface=list(
                request.mix_position_from_liquid_surface
            ),
            mix_speed=list(request.mix_speed),
            mix_surface_following_distance=list(
                request.mix_surface_following_distance
            ),
            limit_curve_index=list(request.limit_curve_index),
            tadm_algorithm=request.tadm_algorithm,
            recording_mode=request.recording_mode,
            use_2nd_section_aspiration=list(request.use_2nd_section_aspiration),
            retract_height_over_2nd_section_to_empty_tip=list(
                request.retract_height_over_2nd_section_to_empty_tip
            ),
            dispensation_speed_during_emptying_tip=list(
                request.dispensation_speed_during_emptying_tip
            ),
            dosing_drive_speed_during_2nd_section_search=list(
                request.dosing_drive_speed_during_2nd_section_search
            ),
            z_drive_speed_during_2nd_section_search=list(
                request.z_drive_speed_during_2nd_section_search
            ),
            cup_upper_edge=list(request.cup_upper_edge),
        )
        return pb2.AspiratePipResponse()

    async def dispense_pip(
        self, request: pb2.DispensePipRequest, ctx: RequestContext
    ) -> pb2.DispensePipResponse:
        await self._backend.dispense_pip(
            tip_pattern=list(request.tip_pattern),
            dispensing_mode=list(request.dispensing_mode),
            x_positions=list(request.x_positions),
            y_positions=list(request.y_positions),
            minimum_height=list(request.minimum_height),
            lld_search_height=list(request.lld_search_height),
            liquid_surface_no_lld=list(request.liquid_surface_no_lld),
            pull_out_distance_transport_air=list(
                request.pull_out_distance_transport_air
            ),
            immersion_depth=list(request.immersion_depth),
            immersion_depth_direction=list(request.immersion_depth_direction),
            surface_following_distance=list(request.surface_following_distance),
            second_section_height=list(request.second_section_height),
            second_section_ratio=list(request.second_section_ratio),
            minimum_traverse_height_at_beginning_of_a_command=request.minimum_traverse_height_at_beginning_of_a_command,
            min_z_endpos=request.min_z_endpos,
            dispense_volumes=list(request.dispense_volumes),
            dispense_speed=list(request.dispense_speed),
            cut_off_speed=list(request.cut_off_speed),
            stop_back_volume=list(request.stop_back_volume),
            transport_air_volume=list(request.transport_air_volume),
            blow_out_air_volume=list(request.blow_out_air_volume),
            lld_mode=list(request.lld_mode),
            side_touch_off_distance=request.side_touch_off_distance,
            dispense_position_above_z_touch_off=list(
                request.dispense_position_above_z_touch_off
            ),
            gamma_lld_sensitivity=list(request.gamma_lld_sensitivity),
            dp_lld_sensitivity=list(request.dp_lld_sensitivity),
            swap_speed=list(request.swap_speed),
            settling_time=list(request.settling_time),
            mix_volume=list(request.mix_volume),
            mix_cycles=list(request.mix_cycles),
            mix_position_from_liquid_surface=list(
                request.mix_position_from_liquid_surface
            ),
            mix_speed=list(request.mix_speed),
            mix_surface_following_distance=list(
                request.mix_surface_following_distance
            ),
            limit_curve_index=list(request.limit_curve_index),
            tadm_algorithm=request.tadm_algorithm,
            recording_mode=request.recording_mode,
        )
        return pb2.DispensePipResponse()

    # ===================================================================
    # Low-level firmware: misc pipetting commands
    # ===================================================================

    async def spread_pip_channels(
        self, request: pb2.SpreadPipChannelsRequest, ctx: RequestContext
    ) -> pb2.SpreadPipChannelsResponse:
        await self._backend.spread_pip_channels()
        return pb2.SpreadPipChannelsResponse()

    async def move_all_pipetting_channels_to_defined_position(
        self,
        request: pb2.MoveAllPipettingChannelsToDefinedPositionRequest,
        ctx: RequestContext,
    ) -> pb2.MoveAllPipettingChannelsToDefinedPositionResponse:
        await self._backend.move_all_pipetting_channels_to_defined_position(
            tip_pattern=request.tip_pattern,
            x_positions=request.x_positions,
            y_positions=request.y_positions,
            minimum_traverse_height_at_beginning_of_command=request.minimum_traverse_height_at_beginning_of_command,
            z_endpos=request.z_endpos,
        )
        return pb2.MoveAllPipettingChannelsToDefinedPositionResponse()

    async def define_tip_needle(
        self, request: pb2.DefineTipNeedleRequest, ctx: RequestContext
    ) -> pb2.DefineTipNeedleResponse:
        await self._backend.define_tip_needle(
            tip_type_table_index=request.tip_type_table_index,
            has_filter=request.has_filter,
            tip_length=request.tip_length,
            maximum_tip_volume=request.maximum_tip_volume,
            tip_size=_PROTO_TO_TIP_SIZE[request.tip_size],
            pickup_method=_PROTO_TO_PICKUP_METHOD[request.pickup_method],
        )
        return pb2.DefineTipNeedleResponse()

    # ===================================================================
    # Probing: liquid heights / volumes
    # ===================================================================

    async def probe_liquid_heights(
        self, request: pb2.ProbeLiquidHeightsRequest, ctx: RequestContext
    ) -> pb2.ProbeLiquidHeightsResponse:
        containers = [
            self._backend.deck.get_resource(name)
            for name in request.container_names
        ]
        use_channels = list(request.use_channels)
        resource_offsets = (
            [coordinate_from_proto(c) for c in request.resource_offsets]
            if len(request.resource_offsets) > 0
            else None
        )
        heights = await self._backend.probe_liquid_heights(
            containers=containers,
            use_channels=use_channels,
            resource_offsets=resource_offsets,
            lld_mode=STARBackend.LLDMode(request.lld_mode),
            search_speed=request.search_speed,
            n_replicates=request.n_replicates,
            move_to_z_safety_after=request.move_to_z_safety_after,
        )
        return pb2.ProbeLiquidHeightsResponse(heights=heights)

    async def probe_liquid_volumes(
        self, request: pb2.ProbeLiquidVolumesRequest, ctx: RequestContext
    ) -> pb2.ProbeLiquidVolumesResponse:
        containers = [
            self._backend.deck.get_resource(name)
            for name in request.container_names
        ]
        use_channels = list(request.use_channels)
        resource_offsets = (
            [coordinate_from_proto(c) for c in request.resource_offsets]
            if len(request.resource_offsets) > 0
            else None
        )
        volumes = await self._backend.probe_liquid_volumes(
            containers=containers,
            use_channels=use_channels,
            resource_offsets=resource_offsets,
            lld_mode=STARBackend.LLDMode(request.lld_mode),
            search_speed=request.search_speed,
            n_replicates=request.n_replicates,
            move_to_z_safety_after=request.move_to_z_safety_after,
        )
        return pb2.ProbeLiquidVolumesResponse(volumes=volumes)

    # ===================================================================
    # Probing: tip presence / status queries
    # ===================================================================

    async def request_tip_presence(
        self, request: pb2.RequestTipPresenceRequest, ctx: RequestContext
    ) -> pb2.RequestTipPresenceResponse:
        tip_presences = await self._backend.request_tip_presence()
        return pb2.RequestTipPresenceResponse(tip_presences=tip_presences)

    async def channels_sense_tip_presence(
        self, request: pb2.ChannelsSenseTipPresenceRequest, ctx: RequestContext
    ) -> pb2.ChannelsSenseTipPresenceResponse:
        tip_presences = await self._backend.channels_sense_tip_presence()
        return pb2.ChannelsSenseTipPresenceResponse(tip_presences=tip_presences)

    async def request_pip_height_last_lld(
        self, request: pb2.RequestPipHeightLastLldRequest, ctx: RequestContext
    ) -> pb2.RequestPipHeightLastLldResponse:
        heights = await self._backend.request_pip_height_last_lld()
        return pb2.RequestPipHeightLastLldResponse(heights=heights)

    async def request_tadm_status(
        self, request: pb2.RequestTadmStatusRequest, ctx: RequestContext
    ) -> pb2.RequestTadmStatusResponse:
        await self._backend.request_tadm_status()
        return pb2.RequestTadmStatusResponse()

    async def request_volume_in_tip(
        self, request: pb2.RequestVolumeInTipRequest, ctx: RequestContext
    ) -> pb2.RequestVolumeInTipResponse:
        volume = await self._backend.request_volume_in_tip(
            channel=request.channel,
        )
        return pb2.RequestVolumeInTipResponse(volume=volume)

    async def request_tip_len_on_channel(
        self, request: pb2.RequestTipLenOnChannelRequest, ctx: RequestContext
    ) -> pb2.RequestTipLenOnChannelResponse:
        length = await self._backend.request_tip_len_on_channel(
            channel_idx=request.channel_idx,
        )
        return pb2.RequestTipLenOnChannelResponse(length=length)

    async def request_probe_z_position(
        self, request: pb2.RequestProbeZPositionRequest, ctx: RequestContext
    ) -> pb2.RequestProbeZPositionResponse:
        z_position = await self._backend.request_probe_z_position(
            channel_idx=request.channel_idx,
        )
        return pb2.RequestProbeZPositionResponse(z_position=z_position)

    # ===================================================================
    # Probing: cLLD / pLLD / z-touch
    # ===================================================================

    async def clld_probe_z_height_using_channel(
        self,
        request: pb2.ClldProbeZHeightUsingChannelRequest,
        ctx: RequestContext,
    ) -> pb2.ClldProbeZHeightUsingChannelResponse:
        kwargs: dict = {}
        lrp = extract_optional_field(request, "lowest_reading_position")
        if lrp is not None:
            kwargs["lowest_immers_pos"] = lrp
        hrp = extract_optional_field(request, "highest_reading_position")
        if hrp is not None:
            kwargs["start_pos_search"] = hrp
        cs = extract_optional_field(request, "channel_speed")
        if cs is not None:
            kwargs["channel_speed"] = cs
        glld = extract_optional_field(request, "gamma_lld_sensitivity")
        if glld is not None:
            kwargs["detection_edge"] = glld
        await self._backend.clld_probe_z_height_using_channel(
            channel_idx=request.channel_idx,
            **kwargs,
        )
        return pb2.ClldProbeZHeightUsingChannelResponse()

    async def plld_probe_z_height_using_channel(
        self,
        request: pb2.PlldProbeZHeightUsingChannelRequest,
        ctx: RequestContext,
    ) -> pb2.PlldProbeZHeightUsingChannelResponse:
        kwargs: dict = {}
        lrp = extract_optional_field(request, "lowest_reading_position")
        if lrp is not None:
            kwargs["lowest_immers_pos"] = lrp
        hrp = extract_optional_field(request, "highest_reading_position")
        if hrp is not None:
            kwargs["start_pos_search"] = hrp
        cs = extract_optional_field(request, "channel_speed")
        if cs is not None:
            kwargs["channel_speed"] = cs
        dplld = extract_optional_field(request, "dp_lld_sensitivity")
        if dplld is not None:
            kwargs["plld_detection_edge"] = dplld
        await self._backend.plld_probe_z_height_using_channel(
            channel_idx=request.channel_idx,
            **kwargs,
        )
        return pb2.PlldProbeZHeightUsingChannelResponse()

    async def ztouch_probe_z_height_using_channel(
        self,
        request: pb2.ZtouchProbeZHeightUsingChannelRequest,
        ctx: RequestContext,
    ) -> pb2.ZtouchProbeZHeightUsingChannelResponse:
        kwargs: dict = {}
        lrp = extract_optional_field(request, "lowest_reading_position")
        if lrp is not None:
            kwargs["lowest_immers_pos"] = lrp
        hrp = extract_optional_field(request, "highest_reading_position")
        if hrp is not None:
            kwargs["start_pos_search"] = hrp
        cs = extract_optional_field(request, "channel_speed")
        if cs is not None:
            kwargs["channel_speed"] = cs
        await self._backend.ztouch_probe_z_height_using_channel(
            channel_idx=request.channel_idx,
            **kwargs,
        )
        return pb2.ZtouchProbeZHeightUsingChannelResponse()

    # ===================================================================
    # Foil piercing
    # ===================================================================

    async def pierce_foil(
        self, request: pb2.PierceFoilRequest, ctx: RequestContext
    ) -> pb2.PierceFoilResponse:
        # The proto defines a low-level positional interface (channel_idx + optional
        # x/y/z positions) while the backend exposes a high-level Well-based API.
        # Compose the operation from available channel primitives.
        ch = request.channel_idx

        xp = extract_optional_field(request, "x_position")
        if xp is not None:
            await self._backend.move_channel_x(ch, x=xp / 10)

        yp = extract_optional_field(request, "y_position")
        if yp is not None:
            await self._backend.position_single_pipetting_channel_in_y_direction(
                pipetting_channel_index=ch + 1, y_position=yp
            )

        z_end = extract_optional_field(request, "z_end_position")
        if z_end is not None:
            await self._backend.move_channel_z(ch, z=z_end / 10)

        return pb2.PierceFoilResponse()

    async def step_off_foil(
        self, request: pb2.StepOffFoilRequest, ctx: RequestContext
    ) -> pb2.StepOffFoilResponse:
        ch = request.channel_idx

        xp = extract_optional_field(request, "x_position")
        if xp is not None:
            await self._backend.move_channel_x(ch, x=xp / 10)

        yp = extract_optional_field(request, "y_position")
        if yp is not None:
            await self._backend.position_single_pipetting_channel_in_y_direction(
                pipetting_channel_index=ch + 1, y_position=yp
            )

        zp = extract_optional_field(request, "z_position")
        if zp is not None:
            await self._backend.move_channel_z(ch, z=zp / 10)

        await self._backend.move_all_channels_in_z_safety()
        return pb2.StepOffFoilResponse()

    async def pierce_foil_high_level(
        self, request: pb2.PierceFoilHighLevelRequest, ctx: RequestContext
    ) -> pb2.PierceFoilHighLevelResponse:
        wells = []
        for name in request.well_names:
            wells.append(self._backend.deck.get_resource(name))
        await self._backend.pierce_foil(
            wells=wells,
            piercing_channels=list(request.piercing_channels),
            hold_down_channels=list(request.hold_down_channels),
            move_inwards=request.move_inwards,
            spread=request.spread,
            one_by_one=request.one_by_one,
            distance_from_bottom=request.distance_from_bottom,
        )
        return pb2.PierceFoilHighLevelResponse()

    # ===================================================================
    # Empty tip(s)
    # ===================================================================

    async def empty_tip(
        self, request: pb2.EmptyTipRequest, ctx: RequestContext
    ) -> pb2.EmptyTipResponse:
        await self._backend.empty_tip(
            channel_idx=request.channel_idx,
            vol=request.holding_volume,
            flow_rate=request.flow_rate,
            acceleration=request.acceleration,
            current_limit=request.current_limit,
        )
        return pb2.EmptyTipResponse()

    async def empty_tips(
        self, request: pb2.EmptyTipsRequest, ctx: RequestContext
    ) -> pb2.EmptyTipsResponse:
        channels = list(request.channels) if len(request.channels) > 0 else None
        await self._backend.empty_tips(
            channels=channels,
            vol=request.holding_volume,
            flow_rate=request.flow_rate,
            acceleration=request.acceleration,
            current_limit=request.current_limit,
        )
        return pb2.EmptyTipsResponse()
