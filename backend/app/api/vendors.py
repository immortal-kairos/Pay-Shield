@router.post("/bulk-approve", response_model=BulkActionResponse)
async def bulk_approve_vendors_route(
    request: BulkVendorActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER, UserRole.ADMIN]))
):
    return await bulk_action_service.bulk_approve_vendors(
        db=db, 
        vendor_ids=request.vendor_ids, 
        current_user=current_user
    )


@router.post("/bulk-reject", response_model=BulkActionResponse)
async def bulk_reject_vendors_route(
    request: BulkRejectVendorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role([UserRole.CHECKER, UserRole.ADMIN]))
):
    return await bulk_action_service.bulk_reject_vendors(
        db=db, 
        vendor_ids=request.vendor_ids, 
        reason=request.rejection_reason, 
        current_user=current_user
    )