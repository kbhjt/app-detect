package com.ruoyi.app.service.impl;

import java.util.List;
import com.ruoyi.common.utils.DateUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.app.mapper.TbDishMapper;
import com.ruoyi.app.domain.TbDish;
import com.ruoyi.app.service.ITbDishService;

/**
 * 菜品管理Service业务层处理
 * 
 * @author ruoyi
 * @date 2025-09-30
 */
@Service
public class TbDishServiceImpl implements ITbDishService 
{
    @Autowired
    private TbDishMapper tbDishMapper;

    /**
     * 查询菜品管理
     * 
     * @param id 菜品管理主键
     * @return 菜品管理
     */
    @Override
    public TbDish selectTbDishById(Long id)
    {
        return tbDishMapper.selectTbDishById(id);
    }

    /**
     * 查询菜品管理列表
     * 
     * @param tbDish 菜品管理
     * @return 菜品管理
     */
    @Override
    public List<TbDish> selectTbDishList(TbDish tbDish)
    {
        return tbDishMapper.selectTbDishList(tbDish);
    }

    /**
     * 新增菜品管理
     * 
     * @param tbDish 菜品管理
     * @return 结果
     */
    @Override
    public int insertTbDish(TbDish tbDish)
    {
        tbDish.setCreateTime(DateUtils.getNowDate());
        return tbDishMapper.insertTbDish(tbDish);
    }

    /**
     * 修改菜品管理
     * 
     * @param tbDish 菜品管理
     * @return 结果
     */
    @Override
    public int updateTbDish(TbDish tbDish)
    {
        tbDish.setUpdateTime(DateUtils.getNowDate());
        return tbDishMapper.updateTbDish(tbDish);
    }

    /**
     * 批量删除菜品管理
     * 
     * @param ids 需要删除的菜品管理主键
     * @return 结果
     */
    @Override
    public int deleteTbDishByIds(Long[] ids)
    {
        return tbDishMapper.deleteTbDishByIds(ids);
    }

    /**
     * 删除菜品管理信息
     * 
     * @param id 菜品管理主键
     * @return 结果
     */
    @Override
    public int deleteTbDishById(Long id)
    {
        return tbDishMapper.deleteTbDishById(id);
    }
}
